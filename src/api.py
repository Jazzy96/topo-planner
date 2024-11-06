import json
import logging
from typing import Dict, Any
from .config import TopologyConfig
from .models import NodeInfo, EdgeInfo, TopologyNode
from .topology_generator import TopologyGenerator
from .exceptions import (
    MeshTopologyError,
    InvalidInputError,
    TopologyGenerationError,
    ChannelAssignmentError,
    ValidationError
)

logger = logging.getLogger(__name__)

def generate_mesh_topology(nodes_json: str, edges_json: str, config_json: str = None) -> str:
    """
    供Java调用的API接口
    
    Args:
        nodes_json: 节点信息的JSON字符串
        edges_json: 边信息的JSON字符串
        config_json: 可选的配置信息JSON字符串
    
    Returns:
        拓扑结果的JSON字符串
    """
    try:
        # 解析输入
        try:
            nodes_data = json.loads(nodes_json)
            edges_data = json.loads(edges_json)
        except json.JSONDecodeError as e:
            raise InvalidInputError(f"JSON解析错误: {str(e)}")
            
        # 验证输入数据
        for node_id, node_info in nodes_data.items():
            try:
                validate_node_data(node_info)
            except ValidationError as e:
                raise ValidationError(f"节点 {node_id} 数据无效: {str(e)}")
                
        for edge_key, edge_info in edges_data.items():
            try:
                validate_edge_data(edge_info)
            except ValidationError as e:
                raise ValidationError(f"边 {edge_key} 数据无效: {str(e)}")
        
        # 转换节点数据
        try:
            nodes: Dict[str, NodeInfo] = {
                node_id: NodeInfo(**node_info)
                for node_id, node_info in nodes_data.items()
            }
        except Exception as e:
            raise InvalidInputError(f"节点数据转换失败: {str(e)}")
        
        # 转换边数据
        try:
            edges: Dict[tuple, EdgeInfo] = {
                tuple(edge_key.split('_')): EdgeInfo(**edge_info)
                for edge_key, edge_info in edges_data.items()
            }
        except Exception as e:
            raise InvalidInputError(f"边数据转换失败: {str(e)}")
        
        # 配置初始化
        config = TopologyConfig()
        if config_json:
            try:
                config_data = json.loads(config_json)
                config = TopologyConfig(**config_data)
            except Exception as e:
                raise InvalidInputError(f"配置数据无效: {str(e)}")
            
        # 生成拓扑
        generator = TopologyGenerator(config)
        topology = generator.generate_topology(nodes, edges)
        
        # 验证生成的拓扑
        if not topology:
            raise TopologyGenerationError("无法生成有效的网络拓扑")
            
        # 转换结果为dict并序列化
        result = {
            node_id: {
                'parent': node.parent,
                'backhaulBand': node.backhaul_band,
                'level': node.level,
                'channel': node.channel,
                'bandwidth': node.bandwidth,
                'maxEirp': node.max_eirp
            }
            for node_id, node in topology.items()
        }
        
        return json.dumps({
            'status': 'success',
            'data': result
        })
        
    except MeshTopologyError as e:
        logger.error(f"拓扑生成错误: {str(e)}", exc_info=True)
        return json.dumps({
            'status': 'error',
            'error_type': e.__class__.__name__,
            'message': str(e)
        })
    except Exception as e:
        logger.error(f"未预期的错误: {str(e)}", exc_info=True)
        return json.dumps({
            'status': 'error',
            'error_type': 'UnexpectedError',
            'message': '系统内部错误'
        })
