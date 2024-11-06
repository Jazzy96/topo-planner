from typing import Dict, Any, Tuple
import json
from .config import TopologyConfig
from .models import NodeInfo, EdgeInfo
from .exceptions import InvalidInputError, ValidationError
from .logger_config import setup_logger

# 配置日志
logger = setup_logger(__name__, '/var/log/topo-planner/topo-planner.log')

def validate_node_data(node_data: Dict[str, Any]) -> None:
    """
    验证节点数据的有效性
    
    Args:
        node_data: 节点数据字典
    
    Raises:
        ValidationError: 当数据验证失败时
    """
    logger.debug(f"开始验证节点数据: {node_data}")
    
    try:
        # 检查必要字段
        required_fields = {'gps', 'load', 'channels', 'max_eirp'}
        missing_fields = required_fields - set(node_data.keys())
        if missing_fields:
            logger.error(f"节点数据缺少必要字段: {missing_fields}")
            raise ValidationError(
                message=f"节点数据缺少必要字段",
                field=list(missing_fields),
                constraints={'required_fields': list(required_fields)}
            )
            
        # 验证GPS数据
        if not isinstance(node_data['gps'], list) or len(node_data['gps']) != 2:
            raise ValidationError(
                message="GPS数据格式无效",
                field='gps',
                value=node_data['gps'],
                constraints={'format': '[latitude, longitude]'}
            )
            
        # 验证load数据
        if not isinstance(node_data['load'], (int, float)) or node_data['load'] < 0:
            raise ValidationError(
                message="负载数据无效",
                field='load',
                value=node_data['load'],
                constraints={'type': 'number', 'min': 0}
            )
            
        # 验证channels数据结构
        if not isinstance(node_data['channels'], dict):
            raise ValidationError(
                message="信道数据格式无效",
                field='channels',
                value=node_data['channels'],
                constraints={'type': 'dict'}
            )
            
        # 验证max_eirp数据结构
        if not isinstance(node_data['max_eirp'], dict):
            raise ValidationError(
                message="最大发射功率数据格式无效",
                field='max_eirp',
                value=node_data['max_eirp'],
                constraints={'type': 'dict'}
            )
            
        logger.debug("节点数据验证通过")
        
    except ValidationError:
        raise
    except Exception as e:
        logger.error(f"节点数据验证过程发生未预期错误: {str(e)}", exc_info=True)
        raise ValidationError(
            message=f"节点数据验证失败: {str(e)}",
            field=None,
            value=node_data
        )

def validate_edge_data(edge_info: Dict[str, Any], edge_key: str) -> None:
    """
    验证边数据的有效性
    
    Args:
        edge_info: 边数据字典
        edge_key: 边的标识符
    
    Raises:
        ValidationError: 当数据验证失败时
    """
    logger.debug(f"开始验证边数据: {edge_key} -> {edge_info}")
    
    try:
        # 检查必要字段
        required_fields = {'rssi_6gh', 'rssi_6gl'}
        missing_fields = required_fields - set(edge_info.keys())
        if missing_fields:
            logger.error(f"边数据缺少必要字段: {missing_fields}")
            raise ValidationError(
                message=f"边数据缺少必要字段",
                field=list(missing_fields),
                constraints={'required_fields': list(required_fields)}
            )
            
        # 验证RSSI数据格式
        for field in ['rssi_6gh', 'rssi_6gl']:
            if not isinstance(edge_info[field], list) or len(edge_info[field]) != 2:
                raise ValidationError(
                    message=f"{field}数据格式无效",
                    field=field,
                    value=edge_info[field],
                    constraints={'format': '[rssi_forward, rssi_backward]'}
                )
            
            # 验证RSSI值范围
            for rssi in edge_info[field]:
                if not isinstance(rssi, (int, float)) or rssi > 0 or rssi < -100:
                    raise ValidationError(
                        message=f"{field}值范围无效",
                        field=field,
                        value=rssi,
                        constraints={'min': -100, 'max': 0}
                    )
                    
        logger.debug("边数据验证通过")
        
    except ValidationError:
        raise
    except Exception as e:
        logger.error(f"边数据验证过程发生未预期错误: {str(e)}", exc_info=True)
        raise ValidationError(
            message=f"边数据验证失败: {str(e)}",
            field=None,
            value=edge_info
        )

def validate_topology_input(nodes_json: str, edges_json: str, config_json: str = None) -> Tuple[Dict[str, NodeInfo], Dict[tuple, EdgeInfo], TopologyConfig]:
    """
    验证并转换拓扑输入数据
    
    Args:
        nodes_json: 节点信息的JSON字符串
        edges_json: 边信息的JSON字符串
        config_json: 可选的配置信息JSON字符串
        
    Returns:
        转换后的节点字典、边字典和配置对象的元组
    """
    try:
        # 解析JSON
        try:
            nodes_data = json.loads(nodes_json)
            edges_data = json.loads(edges_json)
            logger.debug(f"成功解析JSON数据: {len(nodes_data)}个节点, {len(edges_data)}条边")
        except json.JSONDecodeError as e:
            logger.error(f"JSON解析失败: {e}")
            raise InvalidInputError(f"JSON解析错误: {str(e)}")
        
        # 验证节点和边数据
        for node_id, node_info in nodes_data.items():
            validate_node_data(node_info)
        
        for edge_key, edge_info in edges_data.items():
            validate_edge_data(edge_info, edge_key)
            
        # 转换节点数据
        try:
            nodes = {
                node_id: NodeInfo(**node_info)
                for node_id, node_info in nodes_data.items()
            }
        except Exception as e:
            raise InvalidInputError(f"节点数据转换失败: {str(e)}")
            
        # 转换边数据
        try:
            edges = {
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
                
        return nodes, edges, config
        
    except (ValidationError, InvalidInputError):
        raise
    except Exception as e:
        logger.error(f"输入数据验证过程发生未预期错误: {str(e)}", exc_info=True)
        raise InvalidInputError(f"输入数据验证失败: {str(e)}")