from datetime import datetime, timedelta
import inspect
import logging
import pytz
from app.configs.Database import (
    get_db_connection,
    get_db_connection_async,
)
from typing import List
from fastapi import Depends
from app.models.NodeTelemetryDeviceModel import NodeTelemetryDevice
from app.schemas.pydantic.NodeSchema import TelemetryDeviceItem
from sqlalchemy import asc, desc, select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased, Session
from app.utils.ConfigUtil import ConfigUtil
from app.utils.MeshtasticUtil import MeshtasticUtil


class NodeTelemetryDeviceRepository:
    db: Session
    db_async: AsyncSession

    def __init__(
        self,
        db: Session = Depends(get_db_connection),
        db_async: AsyncSession = Depends(get_db_connection_async),
    ) -> None:
        self.config = ConfigUtil().read_config()
        self.db = db
        self.db_async = db_async
        self.logger = logging.getLogger(__name__)

    # 取得某節點 ID 時間區間的遙測資訊 Device
    async def fetch_data_by_time_range(
        self, node_id: int, start: datetime, end: datetime
    ) -> List[TelemetryDeviceItem]:
        try:
            query = await self.db_async.execute(
                select(NodeTelemetryDevice)
                .where(NodeTelemetryDevice.node_id == node_id)
                .where(NodeTelemetryDevice.create_at >= start)
                .where(NodeTelemetryDevice.create_at <= end)
                .order_by(asc(NodeTelemetryDevice.create_at))
            )
            result = query.scalars().all()
            if not result:
                return []

            items: List[TelemetryDeviceItem] = []
            for x in result:
                try:
                    try:
                        viaIdHex = (
                            f"!{MeshtasticUtil.convert_node_id_from_int_to_hex(x.node_id)}"
                            if x.topic.split("/")[-1] == ""
                            else x.topic.split("/")[-1]
                        )
                        viaId = MeshtasticUtil.convert_node_id_from_hex_to_int(viaIdHex)
                    except Exception as e:
                        raise ValueError(f"Invalid topic: {x.topic}")
                    
                    item = TelemetryDeviceItem(
                        batteryLevel=x.battery_level,
                        voltage=x.voltage,
                        channelUtilization=x.channel_utilization,
                        airUtilTx=x.air_util_tx,
                        createAt=x.create_at.astimezone(
                            pytz.timezone(self.config["timezone"])
                        ).isoformat(),
                        updateAt=x.update_at.astimezone(
                            pytz.timezone(self.config["timezone"])
                        ).isoformat(),
                        viaId=viaId,
                        viaIdHex=viaIdHex,
                        channel=MeshtasticUtil.get_channel_from_topic(x.topic),
                        rootTopic=MeshtasticUtil.get_root_topic_from_topic(x.topic),
                    )
                    items.append(item)
                except Exception as e:
                    self.logger.error(
                        f"{inspect.currentframe().f_code.co_name}: {str(e)}"
                    )
                    continue
            return items
        except Exception as e:
            raise Exception(f"{inspect.currentframe().f_code.co_name}: {str(e)}")
