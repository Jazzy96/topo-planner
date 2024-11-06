import json
import logging
from typing import Dict, Any, List, Tuple
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
from .logger_config import setup_logger

logger = setup_logger(__name__, "logs/api.log")

def generate_topology(nodes_json: str, edges_json: str, config_json: str = None) -> str:
    """
    供Java调用的API接口
    
    Args:
        nodes_json: 节点信息的JSON字符串
        edges_json: 边信息的JSON字符串
        config_json: 可选的配置信息JSON字符串
    
    Returns:
        拓扑结果的JSON字符串
    """
    logger.info("开始生成拓扑")
    logger.debug(f"输入参数: nodes_json长度={len(nodes_json)}, "
                f"edges_json长度={len(edges_json)}, "
                f"config_json={'已提供' if config_json else '未提供'}")
    
    try:
        # 解析输入
        try:
            nodes_data = json.loads(nodes_json)
            edges_data = json.loads(edges_json)
            logger.debug(f"成功解析JSON数据: {len(nodes_data)}个节点, {len(edges_data)}条边")
        except json.JSONDecodeError as e:
            logger.error(f"JSON解析失败: {e}")
            raise InvalidInputError(f"JSON解析错误: {str(e)}")
            
        # 验证输入数据
        for node_id, node_info in nodes_data.items():
            try:
                validate_node_data(node_info)
            except ValidationError as e:
                raise ValidationError(f"节点 {node_id} 数据无效: {str(e)}")
                
        for edge_key, edge_info in edges_data.items():
            try:
                validate_edge_data(edge_info, edge_key)
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

def validate_node_data(node_data: Dict[str, Any]) -> None:
    """
    验证节点数据的完整性和有效性
    
    Args:
        node_data: 节点据字典
        
    Raises:
        ValidationError: 当数据验证失败时抛出
    """
    # 1. 检查必要字段
    required_fields = {'gps', 'load', 'channels', 'maxEirp'}
    missing_fields = required_fields - set(node_data.keys())
    if missing_fields:
        raise ValidationError(
            message=f"节点数据缺少必要字段",
            field=list(missing_fields),
            constraints={'required_fields': list(required_fields)}
        )

    # 2. 验证GPS数据
    try:
        gps = node_data['gps']
        if not isinstance(gps, (list, tuple)) or len(gps) != 2:
            raise ValidationError(
                message="GPS数据必须是包含两个元素的数组",
                field='gps',
                value=gps,
                constraints={'type': 'array', 'length': 2}
            )
        if not all(isinstance(coord, (int, float)) for coord in gps):
            raise ValidationError(
                message="GPS坐标必须是数值类型",
                field='gps',
                value=gps,
                constraints={'element_type': 'number'}
            )
        # GPS坐标范围检查
        if not (-90 <= gps[0] <= 90 and -180 <= gps[1] <= 180):
            raise ValidationError(
                message="GPS坐标超出有效范围",
                field='gps',
                value=gps,
                constraints={'latitude': [-90, 90], 'longitude': [-180, 180]}
            )
    except (TypeError, IndexError) as e:
        raise ValidationError(
            message="GPS数据格式无效",
            field='gps',
            value=gps,
            constraints={'type': 'array', 'length': 2}
        )

    # 3. 验证负载数据
    try:
        load = node_data['load']
        if not isinstance(load, (int, float)):
            raise ValidationError(
                message="负载必须是数值类型",
                field='load',
                value=load,
                constraints={'type': 'number'}
            )
        if load < 0:
            raise ValidationError(
                message="负载不能为负值",
                field='load',
                value=load,
                constraints={'minimum': 0}
            )
    except (TypeError, ValueError) as e:
        raise ValidationError(
            message="负载数据格式无效",
            field='load',
            value=load
        )

    # 4. 验证信道数据
    try:
        channels = node_data['channels']
        if not isinstance(channels, dict):
            raise ValidationError(
                message="channels必须是字典类型",
                field='channels',
                value=type(channels).__name__,
                constraints={'type': 'dict'}
            )

        valid_bands = {'6GH', '6GL'}
        valid_bandwidths = {'160M', '80M', '40M', '20M'}
        
        for band, band_data in channels.items():
            if band not in valid_bands:
                raise ValidationError(
                    message=f"无效的频段: {band}",
                    field=f'channels.{band}',
                    value=band,
                    constraints={'valid_values': list(valid_bands)}
                )
                
            if not isinstance(band_data, dict):
                raise ValidationError(
                    message=f"频段{band}的数据必须是字典类型",
                    field=f'channels.{band}',
                    value=type(band_data).__name__,
                    constraints={'type': 'dict'}
                )
                
            for bandwidth, channel_list in band_data.items():
                if bandwidth not in valid_bandwidths:
                    raise ValidationError(
                        message=f"无效的带宽: {bandwidth}",
                        field=f'channels.{band}.{bandwidth}',
                        value=bandwidth,
                        constraints={'valid_values': list(valid_bandwidths)}
                    )
                    
                if not isinstance(channel_list, (list, tuple)):
                    raise ValidationError(
                        message=f"信道列表必须是数组类型",
                        field=f'channels.{band}.{bandwidth}',
                        value=type(channel_list).__name__,
                        constraints={'type': 'array'}
                    )
                    
                if not all(isinstance(ch, int) for ch in channel_list):
                    raise ValidationError(
                        message=f"信道必须是整数类型",
                        field=f'channels.{band}.{bandwidth}',
                        value=channel_list,
                        constraints={'element_type': 'integer'}
                    )
                    
                # 验证信道号范围
                if band == '6GH':
                    if not all(100 <= ch <= 200 for ch in channel_list):
                        raise ValidationError(
                            message="6GH频段信道号超出范围",
                            field=f'channels.{band}.{bandwidth}',
                            value=channel_list,
                            constraints={'range': [100, 200]}
                        )
                else:  # 6GL
                    if not all(1 <= ch <= 100 for ch in channel_list):
                        raise ValidationError(
                            message="6GL频段信道号超出范围",
                            field=f'channels.{band}.{bandwidth}',
                            value=channel_list,
                            constraints={'range': [1, 100]}
                        )
    except (TypeError, KeyError) as e:
        raise ValidationError(
            message="信道数据结构无效",
            field='channels',
            value=str(e)
        )

    # 5. 验证最大发射功率数据
    try:
        max_eirp = node_data['maxEirp']
        if not isinstance(max_eirp, dict):
            raise ValidationError(
                message="maxEirp必须是字典类型",
                field='maxEirp',
                value=type(max_eirp).__name__,
                constraints={'type': 'dict'}
            )
            
        # 验证结构与channels相同
        for band, band_data in max_eirp.items():
            if band not in valid_bands:
                raise ValidationError(
                    message=f"无效的频段: {band}",
                    field=f'maxEirp.{band}',
                    value=band,
                    constraints={'valid_values': list(valid_bands)}
                )
                
            if not isinstance(band_data, dict):
                raise ValidationError(
                    message=f"频段{band}的数据必须是字典类型",
                    field=f'maxEirp.{band}',
                    value=type(band_data).__name__,
                    constraints={'type': 'dict'}
                )
                
            for bandwidth, eirp_list in band_data.items():
                if bandwidth not in valid_bandwidths:
                    raise ValidationError(
                        message=f"无效的带宽: {bandwidth}",
                        field=f'maxEirp.{band}.{bandwidth}',
                        value=bandwidth,
                        constraints={'valid_values': list(valid_bandwidths)}
                    )
                    
                if not isinstance(eirp_list, (list, tuple)):
                    raise ValidationError(
                        message=f"EIRP列表必须是数组类型",
                        field=f'maxEirp.{band}.{bandwidth}',
                        value=type(eirp_list).__name__,
                        constraints={'type': 'array'}
                    )
                    
                if not all(isinstance(e, (int, float)) for e in eirp_list):
                    raise ValidationError(
                        message=f"EIRP值必须是数值类型",
                        field=f'maxEirp.{band}.{bandwidth}',
                        value=eirp_list,
                        constraints={'element_type': 'number'}
                    )
                    
                # 验证EIRP值范围
                if not all(0 <= e <= 36 for e in eirp_list):
                    raise ValidationError(
                        message="EIRP值超出范围",
                        field=f'maxEirp.{band}.{bandwidth}',
                        value=eirp_list,
                        constraints={'range': [0, 36]}
                    )
                    
                # 验证EIRP列表长度与对应的信道列表长度相同
                if len(eirp_list) != len(channels[band][bandwidth]):
                    raise ValidationError(
                        message="EIRP列表长度与信道列表长度不匹配",
                        field=f'maxEirp.{band}.{bandwidth}',
                        value={'eirp_length': len(eirp_list), 
                              'channel_length': len(channels[band][bandwidth])},
                        constraints={'lengths_must_match': True}
                    )
    except (TypeError, KeyError) as e:
        raise ValidationError(
            message="最大发射功率数据结构无效",
            field='maxEirp',
            value=str(e)
        )

def validate_edge_data(edge_data: Dict[str, Any], edge_key: str) -> None:
    """
    验证边数据的完整性和有效性
    
    Args:
        edge_data: 边数据字典
        edge_key: 边的标识符（格式如 "SN0_SN1"）
        
    Raises:
        ValidationError: 当数据验证失败时抛出
    """
    # 1. 检查必要字段
    required_fields = {'rssi_6gh', 'rssi_6gl'}
    missing_fields = required_fields - set(edge_data.keys())
    if missing_fields:
        raise ValidationError(
            message=f"边数据缺少必要字段",
            field=list(missing_fields),
            value=edge_key,
            constraints={'required_fields': list(required_fields)}
        )

    # 2. 验证边标识符格式
    try:
        node1, node2 = edge_key.split('_')
        if not (node1.startswith('SN') and node2.startswith('SN')):
            raise ValidationError(
                message="边标识符格式无效",
                field='edge_key',
                value=edge_key,
                constraints={'format': 'SN{number}_SN{number}'}
            )
    except ValueError:
        raise ValidationError(
            message="边标识符格式无效",
            field='edge_key',
            value=edge_key,
            constraints={'format': 'SN{number}_SN{number}'}
        )

    # 3. 验证RSSI数据格式和值
    for band in ['rssi_6gh', 'rssi_6gl']:
        try:
            rssi_values = edge_data[band]
            
            # 检查RSSI列表格式
            if not isinstance(rssi_values, (list, tuple)):
                raise ValidationError(
                    message=f"{band}必须是数组类型",
                    field=band,
                    value=type(rssi_values).__name__,
                    constraints={'type': 'array', 'length': 2}
                )
                
            # 检查RSSI列表长度
            if len(rssi_values) != 2:
                raise ValidationError(
                    message=f"{band}必须包含两个RSSI值",
                    field=band,
                    value=rssi_values,
                    constraints={'length': 2}
                )
                
            # 检查RSSI值类型
            if not all(isinstance(rssi, int) for rssi in rssi_values):
                raise ValidationError(
                    message=f"{band}的RSSI值必须是整数",
                    field=band,
                    value=rssi_values,
                    constraints={'element_type': 'integer'}
                )
                
            # 检查RSSI值范围
            # 通常RSSI值范围在-100 dBm到0 dBm之间
            if not all(-100 <= rssi <= 0 for rssi in rssi_values):
                raise ValidationError(
                    message=f"{band}的RSSI值超出有效范围",
                    field=band,
                    value=rssi_values,
                    constraints={'range': [-100, 0]}
                )
                
            # 验证RSSI值的合理性
            # 通常两个方向的RSSI差值不会太大（比如超过20dB）
            if abs(rssi_values[0] - rssi_values[1]) > 20:
                raise ValidationError(
                    message=f"{band}的双向RSSI差值过大",
                    field=band,
                    value=rssi_values,
                    constraints={'max_difference': 20}
                )

        except (TypeError, IndexError) as e:
            raise ValidationError(
                message=f"{band}数据格式无效",
                field=band,
                value=str(e)
            )

    # 4. 验证频段间RSSI的一致性
    try:
        rssi_6gh = edge_data['rssi_6gh']
        rssi_6gl = edge_data['rssi_6gl']
        
        # 检查高频和低频RSSI的合理性
        # 通常高频段的RSSI会比低频段弱一些
        for i in range(2):
            if rssi_6gh[i] > rssi_6gl[i]:
                raise ValidationError(
                    message="6GH频段RSSI不应强于6GL频段",
                    field=f'rssi_comparison_{i}',
                    value={'6gh': rssi_6gh[i], '6gl': rssi_6gl[i]},
                    constraints={'rule': '6GH_RSSI <= 6GL_RSSI'}
                )
                
            # 检查高低频RSSI差值的合理性
            # 通常差值不会太大（比如超过15dB）
            if abs(rssi_6gh[i] - rssi_6gl[i]) > 15:
                raise ValidationError(
                    message="高低频段RSSI差值过大",
                    field=f'frequency_difference_{i}',
                    value={'6gh': rssi_6gh[i], '6gl': rssi_6gl[i]},
                    constraints={'max_difference': 15}
                )

    except (KeyError, IndexError) as e:
        raise ValidationError(
            message="RSSI数据比较失败",
            field='rssi_comparison',
            value=str(e)
        )

    # 5. 验证RSSI值的有效性
    # 如果所有RSSI值都太弱（比如都小于-85），可能表示无效连接
    if all(rssi <= -85 for rssi in edge_data['rssi_6gh'] + edge_data['rssi_6gl']):
        raise ValidationError(
            message="所有RSSI值都太弱，可能是无效连接",
            field='rssi_all',
            value={
                'rssi_6gh': edge_data['rssi_6gh'],
                'rssi_6gl': edge_data['rssi_6gl']
            },
            constraints={'minimum_valid_rssi': -85}
        )
