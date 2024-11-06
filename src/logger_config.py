import logging
import os
from datetime import datetime

def setup_logger(name: str, log_file: str = None) -> logging.Logger:
    # 创建logger
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    
    # 创建控制台处理器
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    
    # 创建格式器
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # 设置格式器
    ch.setFormatter(formatter)
    
    # 添加处理器
    logger.addHandler(ch)
    
    return logger 