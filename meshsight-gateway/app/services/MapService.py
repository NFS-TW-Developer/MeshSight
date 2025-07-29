import inspect
import json
import logging
from typing import List, Tuple
from app.exceptions.BusinessLogicException import BusinessLogicException
from datetime import datetime
from fastapi import Depends
from app.models.NodeNeighborEdgeModel import NodeNeighborEdge
from app.models.NodeNeighborInfoModel import NodeNeighborInfo
from app.schemas.pydantic.MapSchema import MapCoordinatesItem, MapCoordinatesResponse
from app.schemas.pydantic.NodeSchema import InfoItem, PostionItem
from app.repositories.NodeInfoRepository import NodeInfoRepository
from app.repositories.NodeNeighborInfoRepository import NodeNeighborInfoRepository
from app.repositories.NodePositionRepository import NodePositionRepository
from app.utils.ConfigUtil import ConfigUtil
from app.utils.MeshtasticUtil import MeshtasticUtil
from app.utils.OtherUtil import OtherUtil


class MapService:

    def __init__(
        self,
        nodeInfoRepository: NodeInfoRepository = Depends(),
        nodeNeighborInfoRepository: NodeNeighborInfoRepository = Depends(),
        nodePositionRepository: NodePositionRepository = Depends(),
    ) -> None:
        self.config = ConfigUtil().read_config()
        self.logger = logging.getLogger(__name__)
        self.nodeInfoRepository = nodeInfoRepository
        self.nodeNeighborInfoRepository = nodeNeighborInfoRepository
        self.nodePositionRepository = nodePositionRepository

    async def coordinates(
        self, start: str, end: str, report_node_hours: int
    ) -> MapCoordinatesResponse:
        try:
            start_time = datetime.fromisoformat(start).replace(second=0, microsecond=0)
            end_time = datetime.fromisoformat(end).replace(second=0, microsecond=0)
        except ValueError:
            raise BusinessLogicException("查詢日期格式錯誤")
        cache_name = f"MapService.coordinates/{start_time.strftime('%Y%m%d%H%M%S')}_{end_time.strftime('%Y%m%d%H%M%S')}_{report_node_hours}"
        cache_json = OtherUtil.read_cache_json(cache_name)
        if cache_json:
            return MapCoordinatesResponse.parse_raw(cache_json)
        try:
            # 取得時間區間更新的節點 ID
            node_ids = await self.nodePositionRepository.fetch_node_ids_by_time_range(
                start_time, end_time
            )

            # 取得節點座標資料
            items: List[MapCoordinatesItem] = []
            for node_id in node_ids:
                try:
                    node_info: InfoItem = (
                        await self.nodeInfoRepository.fetch_node_info_by_node_id(
                            node_id
                        )
                    )
                    node_positions: List[PostionItem] = (
                        await self.nodePositionRepository.fetch_node_position_by_node_id(
                            node_id, 5
                        )
                    )
                    if node_positions is None or len(node_positions) == 0:
                        continue
                    # 取得節點座標最近 X 小時的被誰回報
                    report_node_id = (
                        await self.nodePositionRepository.fetch_node_position_reporters(
                            node_id, report_node_hours
                        )
                    )
                    items.append(
                        MapCoordinatesItem(
                            id=node_id,
                            idHex=f"!{MeshtasticUtil.convert_node_id_from_int_to_hex(node_id)}",
                            info=node_info,
                            positions=node_positions,
                            reportNodeId=report_node_id,
                        )
                    )
                except Exception as e:
                    self.logger.error(
                        f"{inspect.currentframe().f_code.co_name}: {str(e)}"
                    )
                    continue
            # 節點連線
            node_line: List[Tuple[int, int]] = []
            # 節點覆蓋
            node_coverage: List[Tuple[int, int, int]] = []
            for node_a in items:
                node_a_id = node_a.id

                if not node_a.positions or len(node_a.positions) == 0:
                    continue
                node_a_position = node_a.positions[0]

                if not node_a.reportNodeId or len(node_a.reportNodeId) == 0:
                    continue
                node_a_report_ids = node_a.reportNodeId

                for node_b_id in node_a_report_ids:
                    node_b = next((x for x in items if x.id == node_b_id), None)
                    if not node_b:
                        continue
                    if not node_b.positions or len(node_b.positions) == 0:
                        continue
                    node_b_position = node_b.positions[0]
                    if not node_b_position:
                        continue
                    # 計算 A 到 B 的距離
                    distanceA2B = MeshtasticUtil.calculate_distance_in_meters(
                        node_a_position.latitude,
                        node_a_position.longitude,
                        node_b_position.latitude,
                        node_b_position.longitude,
                    )
                    # 檢查是否超過距離限制
                    if distanceA2B > self.config["meshtastic"]["neighborinfo"]["maxDistance"]:
                        continue
                    # 檢查是否沒加入過，則加入節點連線，確保較小的 ID 在前
                    if (
                        min(node_a_id, node_b_id),
                        max(node_a_id, node_b_id),
                    ) not in node_line:
                        # 加入節點連線，確保較小的 ID 在前
                        node_line.append(
                            (min(node_a_id, node_b_id), max(node_a_id, node_b_id))
                        )

                    node_b_report_ids = node_b.reportNodeId
                    if not node_b_report_ids or len(node_b_report_ids) == 0:
                        continue
                    for node_c_id in node_b_report_ids:
                        node_c = next((x for x in items if x.id == node_c_id), None)
                        if not node_c:
                            continue
                        if not node_c.positions or len(node_c.positions) == 0:
                            continue
                        node_c_position = node_c.positions[0]
                        if not node_c_position:
                            continue
                        # 計算 B 到 C 的距離
                        distanceB2C = MeshtasticUtil.calculate_distance_in_meters(
                            node_b_position.latitude,
                            node_b_position.longitude,
                            node_c_position.latitude,
                            node_c_position.longitude,
                        )
                        # 檢查是否超過距離限制
                        if distanceB2C > self.config["meshtastic"]["neighborinfo"]["maxDistance"]:
                            continue
                        # 檢查是否沒加入過
                        if (
                            min(node_b_id, node_c_id),
                            max(node_b_id, node_c_id),
                        ) not in node_line:
                            # 加入節點連線，確保較小的 ID 在前
                            node_line.append(
                                (min(node_b_id, node_c_id), max(node_b_id, node_c_id))
                            )

                        node_c_report_ids = node_c.reportNodeId
                        # 檢查 A 是否在 C 的回報者中，或 C 是否在 A 的回報者中
                        if (
                            node_a_id in node_c_report_ids
                            or node_c_id in node_a_report_ids
                        ):
                            # 檢查 A 到 C 的距離
                            distanceA2C = MeshtasticUtil.calculate_distance_in_meters(
                                node_a_position.latitude,
                                node_a_position.longitude,
                                node_c_position.latitude,
                                node_c_position.longitude,
                            )
                            # 檢查是否超過距離限制
                            if distanceA2C > self.config["meshtastic"]["neighborinfo"]["maxDistance"]:
                                continue
                            # 檢查是否沒加入過
                            sorted_ids = sorted([node_a_id, node_b_id, node_c_id])
                            if sorted_ids not in node_coverage:
                                # 加入節點覆蓋，確保順序為小、中、大
                                node_coverage.append(
                                    (sorted_ids[0], sorted_ids[1], sorted_ids[2])
                                )
            # 節點連線 neighbor_
            node_line_neighbor: List[Tuple[int, int]] = []
            node_neighbor_list: List[Tuple[NodeNeighborInfo, NodeNeighborEdge]] = (
                await self.nodeNeighborInfoRepository.fetch_node_node_neighbor_info_by_time_range(
                    start_time, end_time
                )
            )
            # 遍歷 node_neighbor_list
            for info, edge in node_neighbor_list:
                node_a = next((x for x in items if x.id == edge.node_id), None)
                if not node_a:
                    continue
                node_a_position = node_a.positions[0]
                node_b = next((x for x in items if x.id == edge.edge_node_id), None)
                if not node_b:
                    continue
                node_b_position = node_b.positions[0]
                # 計算 A 到 B 的距離
                distanceA2B = MeshtasticUtil.calculate_distance_in_meters(
                    node_a_position.latitude,
                    node_a_position.longitude,
                    node_b_position.latitude,
                    node_b_position.longitude,
                )
                # 檢查是否超過距離限制
                if distanceA2B > self.config["meshtastic"]["neighborinfo"]["maxDistance"]:
                    continue
                if (
                    min(node_a.id, node_b.id),
                    max(node_a.id, node_b.id),
                ) not in node_line_neighbor:
                    # 加入節點連線，確保較小的 ID 在前
                    node_line_neighbor.append(
                        (min(node_a.id, node_b.id), max(node_a.id, node_b.id))
                    )

            response = MapCoordinatesResponse(
                items=items,
                nodeLine=node_line,
                nodeCoverage=node_coverage,
                nodeLineNeighbor=node_line_neighbor,
            )
            OtherUtil.write_cache_json(
                cache_name, json.dumps(response.dict(), default=str)
            )
            return response
        except BusinessLogicException as e:
            raise Exception(f"{str(e)}")
        except Exception as e:
            self.logger.error(f"{inspect.currentframe().f_code.co_name}: {str(e)}")
            raise Exception("內部伺服器錯誤，請稍後再試")
