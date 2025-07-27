from typing import Optional
from fastapi import APIRouter, Depends
from app.schemas.pydantic.BaseSchema import BaseResponse
from app.services.AppService import AppService
from app.schemas.pydantic.AppSchema import AppSettingDataResponse

router = APIRouter(prefix="/v1/app", tags=["app"])


@router.get(
    "/setting/data",
    response_model=BaseResponse[Optional[AppSettingDataResponse]],
)
async def get_setting_data(
    appService: AppService = Depends(),
):
    try:
        return BaseResponse(
            status="success",
            message="success",
            data=await appService.setting_data(),
        )

    except Exception as e:
        return BaseResponse(
            status="error",
            message=str(e),
            data=None,
        )
