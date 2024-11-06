from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

@dataclass
class NodeInfo:
    gps: Tuple[float, float]
    load: float
    channels: Dict[str, Dict[str, List[int]]]
    max_eirp: Dict[str, Dict[str, List[int]]]

@dataclass
class EdgeInfo:
    rssi_6gh: Tuple[int, int]
    rssi_6gl: Tuple[int, int]

@dataclass
class TopologyNode:
    parent: Optional[str]
    backhaul_band: Optional[str]
    level: int
    channel: List[int]
    bandwidth: List[int]
    max_eirp: List[int] 