import pytz
from app.schemas.pydantic.BaseSchema import BaseResponse
from app.schemas.pydantic.NodeSchema import (
    NodeInfoResponse,
    NodePositionResponse,
    NodeTelemetryDeviceResponse,
)
from app.services.NodeService import NodeService
from app.utils.ConfigUtil import ConfigUtil
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends
from typing import Optional

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
