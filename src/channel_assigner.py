from typing import Dict, List, Set, Tuple, Optional
from collections import defaultdict
from .config import TopologyConfig
from .models import NodeInfo, EdgeInfo, TopologyNode
from .exceptions import ChannelAssignmentError
import logging

# 配置日志
logger = logging.getLogger(__name__)

class ChannelAssigner:
    def __init__(self, config: TopologyConfig):
        self.config = config
        
    def _get_level_nodes(self, 
                         topology: Dict[str, TopologyNode]) -> Dict[int, List[str]]:
        """按层级对节点进行分组"""
        level_nodes = defaultdict(list)
        for node_id, node in topology.items():
            level_nodes[node.level].append(node_id)
        return dict(level_nodes)
        
    def _sort_nodes_by_load(self,
                           nodes: List[str],
                           node_info: Dict[str, NodeInfo]) -> List[str]:
        """按负载对节点进行排序"""
        return sorted(nodes, key=lambda x: node_info[x].load, reverse=True)
        
    def _get_conflict_nodes(self,
                           node_id: str,
                           topology: Dict[str, TopologyNode],
                           edges: Dict[Tuple[str, str], EdgeInfo]) -> Set[str]:
        """获取可能存在信道冲突的节点集合"""
        conflict_nodes = set()
        for (n1, n2), edge in edges.items():
            if node_id not in (n1, n2):
                continue
            other_node = n2 if node_id == n1 else n1
            # 检查RSSI是否超过冲突阈值
            rssi_values = edge.rssi_6gh + edge.rssi_6gl
            if max(rssi_values) >= self.config.RSSI_CONFLICT_THRESHOLD:
                conflict_nodes.add(other_node)
        return conflict_nodes
        
    def _get_available_channels(self,
                              node_id: str,
                              band: str,
                              bandwidth: str,
                              node_info: Dict[str, NodeInfo],
                              conflict_nodes: Set[str],
                              topology: Dict[str, TopologyNode]) -> List[int]:
        """获取可用信道列表"""
        # 获取设备支持的信道
        device_channels = set(node_info[node_id].channels[band][bandwidth])
        
        # 获取冲突设备已使用的信道
        used_channels = set()
        for conflict_node in conflict_nodes:
            if conflict_node in topology and topology[conflict_node].channel:
                used_channels.update(topology[conflict_node].channel)
                
        # 返回可用信道
        return list(device_channels - used_channels)
        
    def _assign_root_channels(self,
                            root_id: str,
                            topology: Dict[str, TopologyNode],
                            node_info: Dict[str, NodeInfo]) -> None:
        """为根节点分配信道"""
        # 为根节点高频分配160M信道
        high_channels = node_info[root_id].channels['6GH']['160M']
        if high_channels:
            topology[root_id].channel.append(high_channels[0])
            topology[root_id].bandwidth.append(160)
            topology[root_id].max_eirp.append(node_info[root_id].max_eirp['6GH']['160M'][0])
            
        # 为根节点低频分配160M信道
        low_channels = node_info[root_id].channels['6GL']['160M']
        if low_channels:
            topology[root_id].channel.append(low_channels[0])
            topology[root_id].bandwidth.append(160)
            topology[root_id].max_eirp.append(node_info[root_id].max_eirp['6GL']['160M'][0])
            
    def _try_assign_channel(self,
                           node_id: str,
                           band: str,
                           topology: Dict[str, TopologyNode],
                           node_info: Dict[str, NodeInfo],
                           edges: Dict[Tuple[str, str], EdgeInfo]) -> bool:
        """尝试为节点分配信道"""
        conflict_nodes = self._get_conflict_nodes(node_id, topology, edges)
        
        # 按带宽从大到小尝试分配
        for bandwidth in ['160M', '80M', '40M', '20M']:
            available_channels = self._get_available_channels(
                node_id, band, bandwidth,
                node_info, conflict_nodes, topology
            )
            
            if available_channels:
                # 分配第一个可用信道
                channel = available_channels[0]
                bw = int(bandwidth[:-1])
                topology[node_id].channel.append(channel)
                topology[node_id].bandwidth.append(bw)
                
                # 获取对应的最大发射功率
                channel_index = node_info[node_id].channels[band][bandwidth].index(channel)
                max_eirp = node_info[node_id].max_eirp[band][bandwidth][channel_index]
                topology[node_id].max_eirp.append(max_eirp)
                
                return True
                
        return False
        
    def assign_channels(self,
                       topology: Dict[str, TopologyNode],
                       nodes: Dict[str, NodeInfo],
                       edges: Dict[Tuple[str, str], EdgeInfo]) -> Dict[str, TopologyNode]:
        """为拓扑中的节点分配信道"""
        try:
            # 验证输入
            if not topology:
                raise ChannelAssignmentError("拓扑结构为空")
                
            # 获取根节点
            try:
                root_id = next(node_id for node_id, node in topology.items() 
                              if node.parent is None)
            except StopIteration:
                raise ChannelAssignmentError("拓扑中未找到根节点")
            
            # 为根节点分配信道
            try:
                self._assign_root_channels(root_id, topology, nodes)
            except Exception as e:
                raise ChannelAssignmentError(f"根节点信道分配失败: {str(e)}")
            
            # 按层次获取节点
            level_nodes = self._get_level_nodes(topology)
            
            # 从第一层开始逐层分配
            for level in sorted(level_nodes.keys())[1:]:
                sorted_nodes = self._sort_nodes_by_load(level_nodes[level], nodes)
                
                for node_id in sorted_nodes:
                    try:
                        parent_id = topology[node_id].parent
                        if parent_id is None:
                            raise ChannelAssignmentError(f"节点 {node_id} 缺少父节点信息")
                        
                        backhaul_band = topology[node_id].backhaul_band
                        if backhaul_band not in ['H', 'L']:
                            raise ChannelAssignmentError(f"节点 {node_id} 的回程频段无效")
                        
                        band = '6GH' if backhaul_band == 'H' else '6GL'
                        
                        # 尝试分配信道
                        success = self._try_assign_channel(node_id, band, topology, nodes, edges)
                        
                        if not success:
                            logger.warning(f"节点 {node_id} 无法分配理想带宽，尝试降级")
                            # 尝试最小带宽
                            if not self._assign_minimum_bandwidth(node_id, band, topology, nodes, edges):
                                raise ChannelAssignmentError(f"节点 {node_id} 无法分配任何有效信道")
                            
                    except Exception as e:
                        raise ChannelAssignmentError(f"节点 {node_id} 信道分配失败: {str(e)}")
                        
            return topology
            
        except Exception as e:
            if isinstance(e, ChannelAssignmentError):
                raise
            raise ChannelAssignmentError(f"信道分配过程发生错误: {str(e)}")