from typing import Optional
import pytz
from datetime import date, datetime, time, timedelta
from fastapi import APIRouter, Depends
from app.schemas.pydantic.BaseSchema import BaseResponse
from app.services.NodeService import NodeService
from app.schemas.pydantic.NodeSchema import NodeInfoResponse, NodeTelemetryDeviceResponse
from app.utils.ConfigUtil import ConfigUtil

config_timezone = pytz.timezone(ConfigUtil().read_config().get("timezone") or "UTC")

router = APIRouter(prefix="/v1/node", tags=["node"])


# 取得節點資訊 info
@router.get("/info/{nodeId}", response_model=BaseResponse[Optional[NodeInfoResponse]])
async def get_info(nodeId: int, nodeService: NodeService = Depends()):
    try:
        return BaseResponse(
            status="success",
            message="success",
            data=await nodeService.info(nodeId),
        )

    except Exception as e:
        return BaseResponse(
            status="error",
            message=str(e),
            data=None,
        )


# 取得節點遙測資訊 device
@router.get(
    "/telemetry/device/{nodeId}",
    response_model=BaseResponse[Optional[NodeTelemetryDeviceResponse]],
)
async def get_telemetry_device(
    nodeId: int,
    start: str = (datetime.now(config_timezone) - timedelta(hours=24)).isoformat(
        timespec="seconds"
    ),
    end: str = datetime.now(config_timezone).isoformat(timespec="seconds"),
    nodeService: NodeService = Depends(),
):
    try:
        return BaseResponse(
            status="success",
            message="success",
            data=await nodeService.telemetry_device(nodeId, start, end),
        )

    except Exception as e:
        return BaseResponse(
            status="error",
            message=str(e),
            data=None,
        )
