from typing import Optional
import pytz
from datetime import date, datetime, time, timedelta
from fastapi import APIRouter, Depends
from app.schemas.pydantic.BaseSchema import BaseResponse
from app.services.MapService import MapService
from app.schemas.pydantic.MapSchema import MapCoordinatesResponse
from app.utils.ConfigUtil import ConfigUtil

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
    mapService: MapService = Depends(),
):
    try:
        return BaseResponse(
            status="success",
            message="success",
            data=await mapService.coordinates(start, end, reportNodeHours),
        )

    except Exception as e:
        return BaseResponse(
            status="error",
            message=str(e),
            data=None,
        )
