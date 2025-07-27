import inspect
import logging
from app.exceptions.BusinessLogicException import BusinessLogicException
from fastapi import Depends
from app.schemas.pydantic.AppSchema import AppSettingDataResponse
from app.repositories.AnalysisDeviceActiveHourlyRepository import (
    AnalysisDeviceActiveHourlyRepository,
)
from app.repositories.NodeInfoRepository import NodeInfoRepository
from app.utils.ConfigUtil import ConfigUtil


class AppService:

    def __init__(
        self,
        analysisDeviceActiveHourlyRepository: AnalysisDeviceActiveHourlyRepository = Depends(),
        nodeInfoRepository: NodeInfoRepository = Depends(),
    ) -> None:
        self.analysisDeviceActiveHourlyRepository = analysisDeviceActiveHourlyRepository
        self.config = ConfigUtil().read_config()
        self.logger = logging.getLogger(__name__)
        self.nodeInfoRepository = nodeInfoRepository

    async def setting_data(self) -> AppSettingDataResponse:
        try:
            return AppSettingDataResponse(
                meshtasticPositionMaxQueryPeriod=self.config["meshtastic"]["position"][
                    "maxQueryPeriod"
                ],
                meshtasticNeighborinfoMaxQueryPeriod=self.config["meshtastic"][
                    "neighborinfo"
                ]["maxQueryPeriod"],
            )
        except BusinessLogicException as e:
            raise Exception(f"{str(e)}")
        except Exception as e:
            self.logger.error(f"{inspect.currentframe().f_code.co_name}: {str(e)}")
            raise Exception("內部伺服器錯誤，請稍後再試")
