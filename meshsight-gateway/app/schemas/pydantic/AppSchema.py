from datetime import datetime
from typing import List
from pydantic import BaseModel


class AppSettingDataResponse(BaseModel):
    meshtasticPositionMaxQueryPeriod: int
    meshtasticNeighborinfoMaxQueryPeriod: int
