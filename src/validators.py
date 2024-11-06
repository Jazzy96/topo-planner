from typing import Dict, Any
from .logger_config import setup_logger
from .exceptions import ValidationError

logger = setup_logger(__name__, '/var/log/topo-planner/topo-planner.log')

def validate_node_data(node_data: Dict[str, Any]) -> None:
    logger.debug(f"开始验证节点数据: {node_data}")
    
    try:
        # 检查必要字段
        logger.debug("检查必要字段")
        required_fields = {'gps', 'load', 'channels', 'maxEirp'}
        missing_fields = required_fields - set(node_data.keys())
        if missing_fields:
            logger.error(f"节点数据缺少必要字段: {missing_fields}")
            raise ValidationError(
                message=f"节点数据缺少必要字段",
                field=list(missing_fields),
                constraints={'required_fields': list(required_fields)}
            )
            
        # GPS验证
        logger.debug(f"验证GPS数据: {node_data['gps']}")
        # ... 其他验证代码 ...
        
        logger.info("节点数据验证成功")
        
    except ValidationError as e:
        logger.error(f"节点数据验证失败: {str(e)}", exc_info=True)
        raise
    except Exception as e:
        logger.error(f"节点数据验证过程发生未预期错误: {str(e)}", exc_info=True)
        raise