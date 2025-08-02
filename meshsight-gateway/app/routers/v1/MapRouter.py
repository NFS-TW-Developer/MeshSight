import pytz
from app.schemas.pydantic.BaseSchema import BaseResponse
from app.schemas.pydantic.MapSchema import MapCoordinatesResponse
from app.services.MapService import MapService
from app.utils.ConfigUtil import ConfigUtil
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends
from typing import Optional

config_timezone = pytz.timezone(ConfigUtil().read_config().get("timezone") or "UTC")

router = APIRouter(prefix="/v1/map", tags=["map"])


# 取得節點座標
@router.get(
    "/coordinates",
    response_model=BaseResponse[Optional[MapCoordinatesResponse]],
)
async def get_coordinates(
    start: str = (datetime.now(config_timezone) - timedelta(hours=24)).isoformat(
        timespec="seconds"
    ),
    end: str = datetime.now(config_timezone).isoformat(timespec="seconds"),
    reportNodeHours: int = 1,
    loraModemPresetList: str = "UNKNOWN,LONG_SLOW,LONG_MOD,LONG_FAST,MEDIUM_SLOW,MEDIUM_FAST,SHORT_SLOW,SHORT_FAST,SHORT_TURBO",
    mapService: MapService = Depends(),
):
    try:
        return BaseResponse(
            status="success",
            message="success",
            data=await mapService.coordinates(
                start, end, reportNodeHours, loraModemPresetList
            ),
        )

    except Exception as e:
        return BaseResponse(
            status="error",
            message=str(e),
            data=None,
        )
