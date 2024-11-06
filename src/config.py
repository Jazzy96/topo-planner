from dataclasses import dataclass

@dataclass
class TopologyConfig:
    MAX_DEGREE: int = 3
    RSSI_THRESHOLD: int = -72
    MAX_HOP: int = 5
    THROUGHPUT_WEIGHT: float = 1.0
    LOAD_WEIGHT: float = 0.5
    HOP_WEIGHT: float = -80.0
    RSSI_CONFLICT_THRESHOLD: int = -85 