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
from app.models.NodePositionModel import NodePosition
from app.schemas.pydantic.NodeSchema import PostionItem
from sqlalchemy import desc, select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased, Session
from app.utils.ConfigUtil import ConfigUtil
from app.utils.MeshtasticUtil import MeshtasticUtil


class NodePositionRepository:
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

    # 取得時間區間更新的節點 ID
    async def fetch_node_ids_by_time_range(
        self, start: datetime, end: datetime
    ) -> List[int]:
        try:
            query = await self.db_async.execute(
                select(NodePosition.node_id)
                .where(
                    NodePosition.update_at
                    >= datetime.now()
                    - timedelta(
                        hours=int(
                            self.config["meshtastic"]["position"]["maxQueryPeriod"]
                        )
                    )
                )  # 限制最大查詢天數
                .where(NodePosition.update_at >= start)
                .where(NodePosition.update_at <= end)
                .distinct(NodePosition.node_id)
            )
            result = query.fetchall()
            return [x.node_id for x in result]
        except Exception as e:
            raise Exception(f"{inspect.currentframe().f_code.co_name}: {str(e)}")

    # 取得節點座標資料
    async def fetch_node_position_by_node_id(
        self, node_id: int, limit: int
    ) -> List[PostionItem]:
        try:
            subquery = aliased(
                select(NodePosition)
                .where(
                    NodePosition.update_at
                    >= datetime.now()
                    - timedelta(
                        hours=int(
                            self.config["meshtastic"]["position"]["maxQueryPeriod"]
                        )
                    )
                )  # 限制最大查詢天數
                .where(NodePosition.node_id == node_id)
                .order_by(NodePosition.topic, desc(NodePosition.update_at))
                .distinct(NodePosition.topic)
                .subquery()
            )

            query = await self.db_async.execute(
                select(subquery).order_by(desc(subquery.c.update_at)).limit(limit)
            )

            result = query.fetchall()
            if not result:
                return []

            items: List[PostionItem] = []
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

                    item = PostionItem(
                        latitude=x.latitude,
                        longitude=x.longitude,
                        altitude=x.altitude,
                        precisionBit=x.precision_bits,
                        precisionInMeters=MeshtasticUtil.convert_precision_to_meter(
                            x.precision_bits
                        ),
                        satsInView=x.sats_in_view,
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
                    self.logger.debug(
                        f"{inspect.currentframe().f_code.co_name}: {str(e)}"
                    )
                    continue
            return items
        except Exception as e:
            raise Exception(f"{inspect.currentframe().f_code.co_name}: {str(e)}")

    # 取得節點座標最近 X 小時的被誰回報
    async def fetch_node_position_reporters(
        self, node_id: int, hours: int = 1
    ) -> List[int]:
        try:
            subquery = aliased(
                select(NodePosition)
                .where(
                    NodePosition.update_at
                    >= datetime.now()
                    - timedelta(
                        hours=int(
                            self.config["meshtastic"]["position"]["maxQueryPeriod"]
                        )
                    )
                )  # 限制最大查詢天數
                .where(NodePosition.node_id == node_id)
                .where(
                    NodePosition.update_at >= datetime.now() - timedelta(hours=hours)
                )
                .distinct(NodePosition.topic)
                .subquery()
            )

            query = await self.db_async.execute(select(subquery))
            result = query.fetchall()
            if not result:
                return []

            items: List[int] = []
            for x in result:
                if x.topic and "/" in x.topic and x.topic.split("/")[-1] != "":
                    try:
                        node_id = MeshtasticUtil.convert_node_id_from_hex_to_int(
                            x.topic.split("/")[-1]
                        )
                    except Exception as e:
                        self.logger.debug(
                            f"{inspect.currentframe().f_code.co_name}: {str(e)}"
                        )
                        continue
                    if node_id not in items:
                        items.append(node_id)
            return items
        except Exception as e:
            raise Exception(f"{inspect.currentframe().f_code.co_name}: {str(e)}")
