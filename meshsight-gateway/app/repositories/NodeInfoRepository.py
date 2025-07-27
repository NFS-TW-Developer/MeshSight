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
from app.models.NodeInfoModel import NodeInfo
from app.schemas.pydantic.AnalysisSchema import AnalysisDistributionItem
from app.schemas.pydantic.NodeSchema import InfoItem
from sqlalchemy import desc, select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session
from app.utils.ConfigUtil import ConfigUtil


class NodeInfoRepository:
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

    async def fetch_distribution_firmware(self) -> List[AnalysisDistributionItem]:
        query = await self.db_async.execute(
            select(
                func.coalesce(NodeInfo.firmware_version, "Unknown").label(
                    "firmware_version"
                ),
                func.count(func.coalesce(NodeInfo.firmware_version, "Unknown")).label(
                    "count"
                ),
            )
            .where(NodeInfo.update_at >= datetime.now() - timedelta(days=1))
            .group_by("firmware_version")
            .order_by(desc("count"))
        )
        result = query.fetchall()
        items: List[AnalysisDistributionItem] = [
            AnalysisDistributionItem(name=x.firmware_version, count=x.count)
            for x in result
        ]
        return items

    async def fetch_distribution_hardware(self) -> List[AnalysisDistributionItem]:
        query = await self.db_async.execute(
            select(
                func.coalesce(NodeInfo.hw_model, "Unknown").label("hw_model"),
                func.count(func.coalesce(NodeInfo.hw_model, "Unknown")).label("count"),
            )
            .where(NodeInfo.update_at >= datetime.now() - timedelta(days=1))
            .group_by("hw_model")
            .order_by(desc("count"))
        )
        result = query.fetchall()
        items: List[AnalysisDistributionItem] = [
            AnalysisDistributionItem(name=x.hw_model, count=x.count) for x in result
        ]
        return items

    async def fetch_distribution_role(self) -> List[AnalysisDistributionItem]:
        query = await self.db_async.execute(
            select(
                func.coalesce(NodeInfo.role, "Unknown").label("role"),
                func.count(func.coalesce(NodeInfo.role, "Unknown")).label("count"),
            )
            .where(NodeInfo.update_at >= datetime.now() - timedelta(days=1))
            .group_by("role")
            .order_by(desc("count"))
        )
        result = query.fetchall()
        items: List[AnalysisDistributionItem] = [
            AnalysisDistributionItem(name=x.role, count=x.count) for x in result
        ]
        return items

    async def fetch_node_info_by_node_id(self, node_id: int) -> InfoItem:
        try:
            query = await self.db_async.execute(
                select(NodeInfo).where(NodeInfo.node_id == node_id)
            )
            result = query.fetchone()
            if not result:
                return None
            result = result[0]
            return InfoItem(
                longName=result.long_name,
                shortName=result.short_name,
                hardware=result.hw_model,
                isLicensed=result.is_licensed,
                role=result.role,
                firmware=result.firmware_version,
                loraRegion=result.lora_region,
                loraModemPreset=result.lora_modem_preset,
                hasDefaultChannel=result.has_default_channel,
                numOnlineLocalNodes=result.num_online_local_nodes,
                updateAt=result.update_at.astimezone(
                    pytz.timezone(self.config["timezone"])
                ).isoformat(),
                channel=(
                    f"{result.topic.split('/')[-2]}(MapReport)"
                    if result.topic.split("/")[-2] == "map"
                    else (
                        f"{result.topic.split('/')[-2]}(json)"
                        if result.topic.split("/")[-3] == "json"
                        else result.topic.split("/")[-2]
                    )
                ),
                rootTopic=f"{result.topic.split('/')[0]}/{result.topic.split('/')[1]}",
            )

        except Exception as e:
            raise Exception(f"{inspect.currentframe().f_code.co_name}: {str(e)}")
