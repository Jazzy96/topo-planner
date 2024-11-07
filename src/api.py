import json
import logging
from typing import Dict
from .config import TopologyConfig
from .models import NodeInfo, EdgeInfo
from .topology_generator import TopologyGenerator
from .exceptions import MeshTopologyError, InvalidInputError, TopologyGenerationError
from .validators import validate_topology_input
from .logger_config import setup_logger
import os
from datetime import datetime

logger = setup_logger(__name__, '/var/log/topo-planner/topo-planner.log')

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
        # 验证并转换输入数据
        nodes, edges, config = validate_topology_input(nodes_json, edges_json, config_json)
            
        # 生成拓扑
        generator = TopologyGenerator(config)
        topology = generator.generate(nodes, edges)
        
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
                'maxEirp': node.max_eirp,
                'gps': node.gps
            }
            for node_id, node in topology.items()
        }

        node_count = len(nodes)
        save_topology_result(json.dumps({
            'status': 'success',
            'data': result
        }), node_count)
        
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

def save_topology_result(result: str, node_count: int) -> str:
    """保存拓扑结果到文件"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"topology_{node_count}nodes_{timestamp}.json"
    result_dir = "/app/results"
    
    # 确保目录存在
    os.makedirs(result_dir, exist_ok=True)
    
    filepath = os.path.join(result_dir, filename)
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(result)
        
    return filename

def get_timestamp_from_filename(filename: str) -> datetime:
    """从文件名中提取时间戳"""
    try:
        # 从文件名中提取日期时间部分
        timestamp_str = filename.split('_')[2].split('.')[0]
        return datetime.strptime(timestamp_str, '%Y%m%d_%H%M%S')
    except (IndexError, ValueError):
        # 如果解析失败，返回一个很早的日期
        return datetime.min

def list_topology_results():
    """列出所有拓扑结果文件，按时间戳排序"""
    result_dir = "/app/results"
    results = []
    
    for filename in os.listdir(result_dir):
        if filename.startswith('topology_') and filename.endswith('.json'):
            filepath = os.path.join(result_dir, filename)
            with open(filepath, 'r', encoding='utf-8') as f:
                try:
                    data = json.load(f)
                    results.append({
                        'filename': filename,
                        'data': data,
                        'timestamp': get_timestamp_from_filename(filename)
                    })
                except json.JSONDecodeError:
                    logger.error(f"无法解析文件 {filename}")
                    continue
    
    # 按时间戳排序
    results.sort(key=lambda x: x['timestamp'], reverse=True)
    
    # 移除timestamp字段，因为前端不需要
    for result in results:
        del result['timestamp']
    
    return results
