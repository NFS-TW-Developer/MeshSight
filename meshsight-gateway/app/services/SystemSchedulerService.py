import logging
import os
from app.configs.Database import get_db_connection_async
from datetime import datetime, timedelta, timezone
from app.models.AnalysisDeviceActiveHourlyModel import AnalysisDeviceActiveHourly
from app.models.NodeModel import Node
from app.models.NodeInfoModel import NodeInfo
from app.models.NodeNeighborInfoModel import NodeNeighborInfo
from app.models.NodePositionModel import NodePosition
from sqlalchemy import delete
from sqlalchemy.future import select
from sqlalchemy.orm import aliased
from app.utils.ConfigUtil import ConfigUtil


class SystemSchedulerService:

    def __init__(self) -> None:
        self.config = ConfigUtil().read_config()
        self.logger = logging.getLogger(__name__)

    # 分析當下小時，前一小時的活躍裝置數量，並存入資料庫
    async def analyze_active_device(self):
        try:
            # 取得前一小時時間
            last_hour = datetime.now(timezone.utc).replace(
                minute=0, second=0, microsecond=0
            ) - timedelta(hours=1)

            async for session in get_db_connection_async():
                try:
                    # 檢查該 hourly 是否已經存在
                    existing_record = await session.execute(
                        select(AnalysisDeviceActiveHourly).filter(
                            AnalysisDeviceActiveHourly.hourly == last_hour
                        )
                    )
                    existing_record = existing_record.scalars().first()

                    if existing_record:
                        self.logger.error(f"記錄已存在於 {last_hour}")
                        return

                    # 取得前一小時的活躍節點，並聯結 NodeInfo 表
                    node_info_alias = aliased(NodeInfo)
                    result = await session.execute(
                        select(Node, node_info_alias.uuid.label("node_info_uuid"))
                        .outerjoin(node_info_alias, Node.id == node_info_alias.node_id)
                        .filter(Node.last_heard_at >= last_hour)
                    )
                    rows = result.all()

                    # 根據如果節點有在 NodeInfo 表，則 known_count + 1 否則 unknown_count + 1
                    known_count = 0
                    unknown_count = 0
                    for row in rows:
                        node, node_info_uuid = row
                        if node_info_uuid:
                            known_count += 1
                        else:
                            unknown_count += 1

                    # 將結果插入到 AnalysisDeviceActiveHourly 表中
                    new_record = AnalysisDeviceActiveHourly(
                        hourly=last_hour,
                        known_count=known_count,
                        unknown_count=unknown_count,
                    )
                    session.add(new_record)
                    await session.commit()
                    self.logger.info(f"成功插入記錄於 {last_hour}")
                except Exception as inner_e:
                    self.logger.error(f"處理資料庫操作時發生錯誤: {inner_e}")
                    await session.rollback()
                finally:
                    await session.close()
        except Exception as e:
            self.logger.error(f"分析活躍裝置數量時發生錯誤: {e}")

    # 清理 cache 檔案
    async def clear_cache(self):
        try:
            # 取得 cache 路徑
            cache_path = self.config["cache"]["path"]
            # 清理 cache 檔案，只保留最近 1 天的檔案
            for filename in os.listdir(cache_path):
                file_path = os.path.join(cache_path, filename)
                if os.path.isfile(file_path):
                    file_time = os.path.getmtime(file_path)
                    if file_time < datetime.now().timestamp() - 86400:
                        os.remove(file_path)
                        self.logger.debug(f"已清理 cache 檔案: {filename}")
        except Exception as e:
            self.logger.error(f"清理 cache 檔案時發生錯誤: {e}")

    # 清理超過期限的 node_neighbor_info 資料
    async def clear_node_neighbor_info(self):
        try:
            # 取得 node_neighbor_info 資料的過期時間
            node_neighbor_info_expire = self.config["meshtastic"]["neighborinfo"]["expire"]
            expire_time = datetime.now() - timedelta(hours=node_neighbor_info_expire)
            
            async for session in get_db_connection_async():
                try:
                    # 刪除過期的 node_neighbor_info 資料
                    delete_stmt = delete(NodeNeighborInfo).where(NodeNeighborInfo.update_at < expire_time)
                    result = await session.execute(delete_stmt)
                    await session.commit()
                    self.logger.debug(f"已清理 {result.rowcount} 筆 node_neighbor_info 資料")
                except Exception as inner_e:
                    self.logger.error(f"處理資料庫操作時發生錯誤: {inner_e}")
                    await session.rollback()
                finally:
                    await session.close()
        except Exception as e:
            self.logger.error(f"清理 node_neighbor_info 資料時發生錯誤: {e}")

    # 清理超過期限的 node_position 資料
    async def clear_node_position(self):
        try:
            # 取得 node_position 資料的過期時間
            node_position_expire = self.config["meshtastic"]["position"]["expire"]
            expire_time = datetime.now() - timedelta(hours=node_position_expire)
            
            async for session in get_db_connection_async():
                try:
                    # 刪除過期的 node_position 資料
                    delete_stmt = delete(NodePosition).where(NodePosition.update_at < expire_time)
                    result = await session.execute(delete_stmt)
                    await session.commit()
                    self.logger.debug(f"已清理 {result.rowcount} 筆 node_neighbor_info 資料")
                except Exception as inner_e:
                    self.logger.error(f"處理資料庫操作時發生錯誤: {inner_e}")
                    await session.rollback()
                finally:
                    await session.close()
        except Exception as e:
            self.logger.error(f"清理 node_position 資料時發生錯誤: {e}")
