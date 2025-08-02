import json
from typing import List, Optional, Tuple
from pydantic import BaseModel
from .NodeSchema import InfoItem, PositionItem


class MapCoordinatesItem(BaseModel):
    id: int  # ID
    idHex: str  # ID HEX
    info: Optional[InfoItem]  # 資訊
    positions: List[PositionItem]  # 節點座標
    reportNodeId: List[int]  # 回報節點 ID


class MapCoordinatesResponse(BaseModel):
    items: List[MapCoordinatesItem]
    nodeLine: List[Tuple[int, int]]
    nodeCoverage: List[Tuple[int, int, int]]
    nodeLineNeighbor: List[Tuple[int, int]]

    @classmethod
    def parse_raw(cls, data):
        return cls.parse_obj(json.loads(data))
