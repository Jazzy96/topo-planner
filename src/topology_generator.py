from typing import Dict, List, Set, Tuple, Optional
import heapq
from .config import TopologyConfig
from .models import NodeInfo, EdgeInfo, TopologyNode
from .exceptions import TopologyGenerationError
import logging
from .channel_assigner import ChannelAssigner
from .logger_config import setup_logger

# 配置日志
logger = setup_logger(__name__, "logs/topology_generator.log")

class TopologyGenerator:
    def __init__(self, config: TopologyConfig):
        self.config = config
        logger.info(f"初始化拓扑生成器，配置参数: {config}")
    
    def _predict_throughput(self, rssi: int) -> float:
        """根据RSSI预测吞吐量的简单线性模型"""
        logger.debug(f"预测吞吐量 - 输入RSSI: {rssi}")
        throughput = max(0, (rssi + 100) * 10)  # 简单示例：RSSI=-70时吞吐量为300Mbps
        logger.debug(f"预测吞吐量结果: {throughput}Mbps")
        return throughput
    
    def _calculate_edge_weight(self,
                             parent: str,
                             child: str,
                             nodes: Dict[str, NodeInfo],
                             edges: Dict[Tuple[str, str], EdgeInfo],
                             current_tree: Dict[str, TopologyNode]) -> float:
        """计算边的权重"""
        logger.debug(f"计算边权重 - 父节点: {parent}, 子节点: {child}")
        
        edge = edges.get((parent, child)) or edges.get((child, parent))
        if not edge:
            logger.warning(f"未找到边连接: {parent}-{child}")
            return float('-inf')
        
        # 获取最好的RSSI值
        rssi = max(edge.rssi_6gh + edge.rssi_6gl)
        logger.debug(f"最大RSSI值: {rssi}")
        
        # 计算预测吞吐量
        throughput = self._predict_throughput(rssi)
        logger.debug(f"预测吞吐量: {throughput}")
        
        # 计算节点负载
        total_load = nodes[parent].load + nodes[child].load
        logger.debug(f"总负载: {total_load}")
        
        # 计算父节点跳数
        parent_hops = current_tree[parent].level if parent in current_tree else 0
        logger.debug(f"父节点跳数: {parent_hops}")
        
        # 加权计算
        weight = (self.config.THROUGHPUT_WEIGHT * throughput +
                 self.config.LOAD_WEIGHT * total_load +
                 self.config.HOP_WEIGHT * parent_hops)
        
        logger.info(f"边权重计算完成: {parent}-{child}, 权重={weight}")
        return weight
    
    def _check_rssi_constraint(self, edge: EdgeInfo) -> bool:
        """检查RSSI约束"""
        return (max(edge.rssi_6gh + edge.rssi_6gl) >= self.config.RSSI_THRESHOLD)
    
    def _check_frequency_constraint(self,
                                  parent: str,
                                  current_tree: Dict[str, TopologyNode]) -> bool:
        """检查异频约束"""
        if parent not in current_tree:
            return True
        # 实际实现需要检查频段冲突
        return True
    
    def _check_degree_constraint(self,
                               parent: str,
                               current_tree: Dict[str, TopologyNode]) -> bool:
        """检查度约束"""
        if parent not in current_tree:
            return True
        child_count = sum(1 for node in current_tree.values() if node.parent == parent)
        return child_count < self.config.MAX_DEGREE
    
    def _check_hop_constraint(self,
                            parent: str,
                            current_tree: Dict[str, TopologyNode]) -> bool:
        """检查跳数约束"""
        if parent not in current_tree:
            return True
        return current_tree[parent].level < self.config.MAX_HOP
    
    def _check_constraints(self,
                          parent: str,
                          child: str,
                          nodes: Dict[str, NodeInfo],
                          edges: Dict[Tuple[str, str], EdgeInfo],
                          current_tree: Dict[str, TopologyNode]) -> bool:
        """检查所有约束条件"""
        edge = edges.get((parent, child)) or edges.get((child, parent))
        if not edge:
            return False
            
        return (self._check_rssi_constraint(edge) and
                self._check_frequency_constraint(parent, current_tree) and
                self._check_degree_constraint(parent, current_tree) and
                self._check_hop_constraint(parent, current_tree))
    
    def _generate_tree(self,
                      nodes: Dict[str, NodeInfo],
                      edges: Dict[Tuple[str, str], EdgeInfo]) -> Dict[str, TopologyNode]:
        """使用改进的Prim算法生成最大生成树"""
        try:
            if not nodes:
                raise TopologyGenerationError("节点列表为空")
                
            root_node = next(iter(nodes))
            selected: Set[str] = {root_node}
            unselected = set(nodes.keys()) - selected
            
            # 初始化树结构
            tree: Dict[str, TopologyNode] = {
                root_node: TopologyNode(
                    parent=None,
                    backhaul_band=None,
                    level=0,
                    channel=[],
                    bandwidth=[],
                    max_eirp=[]
                )
            }
            
            iteration_count = 0
            max_iterations = len(nodes) * 2  # 防止无限循环
            
            while unselected and iteration_count < max_iterations:
                best_edge = self._find_best_edge(selected, unselected, nodes, edges, tree)
                if not best_edge:
                    logger.warning(f"无法找到更多有效边，剩余 {len(unselected)} 个未连接节点")
                    break
                    
                parent, child, weight = best_edge
                
                # 验证边的有效性
                if weight <= float('-inf'):
                    raise TopologyGenerationError(f"检测到无效的边权重: {parent}-{child}")
                    
                # 确定回程频段
                parent_level = tree[parent].level
                backhaul_band = 'H' if parent_level % 2 == 0 else 'L'
                
                # 更新树结构
                tree[child] = TopologyNode(
                    parent=parent,
                    backhaul_band=backhaul_band,
                    level=parent_level + 1,
                    channel=[],
                    bandwidth=[],
                    max_eirp=[]
                )
                
                # 更新节点集合
                selected.add(child)
                unselected.remove(child)
                iteration_count += 1
                
            if iteration_count >= max_iterations:
                raise TopologyGenerationError("超过最大迭代次数限制")
                
            if unselected:
                logger.warning(f"存在未连接的节点: {unselected}")
                
            return tree
            
        except Exception as e:
            if isinstance(e, TopologyGenerationError):
                raise
            raise TopologyGenerationError(f"生成树过程发生错误: {str(e)}")
    
    def _find_best_edge(self,
                        selected: Set[str],
                        unselected: Set[str],
                        nodes: Dict[str, NodeInfo],
                        edges: Dict[Tuple[str, str], EdgeInfo],
                        current_tree: Dict[str, TopologyNode]) -> Optional[Tuple[str, str, float]]:
        """
        找到最佳边
        
        Args:
            selected: 已选择的节点集合
            unselected: 未选择的节点集合
            nodes: 所有节点信息
            edges: 所有边信息
            current_tree: 当前已生成的树结构
            
        Returns:
            最佳边的三元组 (父节点, 子节点, 权重)，如果没有合法边则返回None
        """
        valid_edges = []
        
        # 遍历所有可能的边
        for parent in selected:
            for child in unselected:
                # 检查是否存在这条边（考虑双向）
                edge_key = (parent, child)
                reverse_edge_key = (child, parent)
                
                if edge_key not in edges and reverse_edge_key not in edges:
                    continue
                    
                # 检查所有约束条件
                if not self._check_constraints(parent, child, nodes, edges, current_tree):
                    continue
                    
                # 计算边的权重
                weight = self._calculate_edge_weight(parent, child, nodes, edges, current_tree)
                
                # 将合法边加入候选集合
                # 使用负权重是因为heapq实现的是最小堆，而我们需要最大权重
                heapq.heappush(valid_edges, (-weight, parent, child))
        
        # 如果没有合法边，返回None
        if not valid_edges:
            return None
            
        # 返回权重最大的边
        # heapq.heappop返回的是(-weight, parent, child)
        # 我们需要转换回正权重并返回(parent, child, weight)的格式
        neg_weight, parent, child = heapq.heappop(valid_edges)
        return (parent, child, -neg_weight)