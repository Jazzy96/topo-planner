class MeshTopologyError(Exception):
    """网状拓扑相关错误的基类"""
    def __init__(self, message: str, details: dict = None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message)

    def __str__(self):
        if self.details:
            return f"{self.message} - 详细信息: {self.details}"
        return self.message

class InvalidInputError(MeshTopologyError):
    """输入数据无效的错误
    
    Attributes:
        field: 出错的字段名
        value: 导致错误的值
        requirement: 期望的要求
    """
    def __init__(self, message: str, field: str = None, value: any = None, requirement: str = None):
        details = {
            'field': field,
            'value': value,
            'requirement': requirement
        }
        super().__init__(message, details)

class TopologyGenerationError(MeshTopologyError):
    """拓扑生成过程中的错误
    
    Attributes:
        phase: 出错的阶段
        node_id: 相关的节点ID
        current_state: 出错时的状态信息
    """
    def __init__(self, message: str, phase: str = None, node_id: str = None, current_state: dict = None):
        details = {
            'phase': phase,
            'node_id': node_id,
            'current_state': current_state
        }
        super().__init__(message, details)

class ChannelAssignmentError(MeshTopologyError):
    """信道分配过程中的错误
    
    Attributes:
        node_id: 出错的节点ID
        band: 相关的频段
        attempted_channels: 尝试过的信道
        conflict_nodes: 冲突的节点列表
    """
    def __init__(self, message: str, node_id: str = None, band: str = None, 
                 attempted_channels: list = None, conflict_nodes: list = None):
        details = {
            'node_id': node_id,
            'band': band,
            'attempted_channels': attempted_channels,
            'conflict_nodes': conflict_nodes
        }
        super().__init__(message, details)

class ValidationError(MeshTopologyError):
    """数据验证错误
    
    Attributes:
        field: 验证失败的字段
        value: 无效的值
        constraints: 验证约束条件
        context: 额外的上下文信息
    """
    def __init__(self, message: str, field: str = None, value: any = None, 
                 constraints: dict = None, context: dict = None):
        details = {
            'field': field,
            'value': value,
            'constraints': constraints,
            'context': context
        }
        super().__init__(message, details) 