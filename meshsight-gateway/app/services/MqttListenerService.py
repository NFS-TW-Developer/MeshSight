import base64
from datetime import datetime, timezone
import json
import math
import numbers
import aiomqtt
import asyncio
import inspect
import logging
from app.configs.Database import (
    get_db_connection_async
)
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from google.protobuf.json_format import MessageToJson, Parse

try:
    from meshtastic.protobuf import mesh_pb2, mqtt_pb2, portnums_pb2, telemetry_pb2
    from meshtastic import BROADCAST_NUM
except ImportError:
    from meshtastic import (
        mesh_pb2,
        mqtt_pb2,
        portnums_pb2,
        telemetry_pb2,
        BROADCAST_NUM,
    )
from app.models.NodeInfoModel import NodeInfo
from app.models.NodeModel import Node
from app.models.NodeNeighborEdgeModel import NodeNeighborEdge
from app.models.NodeNeighborInfoModel import NodeNeighborInfo
from app.models.NodePositionModel import NodePosition
from app.models.NodeTelemetryAirQualityModel import NodeTelemetryAirQuality
from app.models.NodeTelemetryDeviceModel import NodeTelemetryDevice
from app.models.NodeTelemetryEnvironmentModel import NodeTelemetryEnvironment
from app.models.NodeTelemetryPowerModel import NodeTelemetryPower
from sqlalchemy import delete, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.future import select
from app.utils.ConfigUtil import ConfigUtil
from app.utils.MeshtasticUtil import MeshtasticUtil


class MqttListenerService:
    def __init__(self) -> None:
        self.config = ConfigUtil().read_config()
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(self.config.get("log", {}).get("level", "INFO").upper())

    async def start(self):
        tasks = []
        # 讀取設定檔
        for mqtt_client in self.config["mqtt"]["client"]:
            tasks.append(self.handle_client(mqtt_client))
        await asyncio.gather(*tasks)

    async def handle_client(self, client_config):
        tasks = []
        for host in client_config["hosts"]:
            tasks.append(self.subscribe_to_host(client_config, host))
        await asyncio.gather(*tasks)

    async def subscribe_to_host(self, client_config, host):
        while True:
            try:
                async with aiomqtt.Client(
                    hostname=host,
                    port=client_config["port"],
                    identifier=client_config["identifier"],
                    username=client_config["username"],
                    password=client_config["password"],
                ) as client:
                    # 訂閱多個主題
                    for topic in client_config["topics"]:
                        await client.subscribe(topic)
                    self.logger.info(f"已訂閱 {host} 的主題: {client_config['topics']}")
                    async for message in client.messages:
                        await self.on_message(client, None, message)
            except Exception as e:
                if client_config["showErrorLog"]:
                    self.logger.error(f"{inspect.currentframe().f_code.co_name}: {e}")
                    self.logger.error(f"{host} 訂閱服務發生錯誤，正在重試...")
                await asyncio.sleep(client_config["retryTime"])  # 等待一段時間後重試
                continue  # 繼續嘗試訂閱該主機

    async def on_message(self, client, userdata, message):
        try:
            # 處理訊息邏輯
            topic: str = message.topic.value
            # 排除含以下內容的 topic
            if "#" in topic:
                self.logger.error(f"Ignoring invalid topic with #: {topic}")
                return
            elif "/2/stat/" in topic:
                # Meshtastic Firmware 2.4.1.394e0e1 開始棄用
                return

            # 解析訊息
            message_json = {}
            if "/2/json/" in topic:
                try:
                    message_json = json.loads(
                        message.payload.decode("utf-8")
                    )  # 嘗試使用 UTF-8 解碼
                except UnicodeDecodeError:
                    logging.error(
                        f"Failed to decode message payload as UTF-8: {message.payload}"
                    )
                    return
                message_json["topic"] = topic
                if message_json.get("type") == "nodeinfo":
                    # raise Exception(f"NODEINFO 收 {message_json['payload']}")
                    # 將收到的 nodeinfo 資料轉換為 NodeInfo
                    # 資料範例: {'hardware': 255, 'id': '!b1231321', 'longname': 'Mydevuce', 'role': 0, 'shortname': 'devs'}
                    payload = message_json["payload"]
                    node_info = mesh_pb2.User()
                    node_info.id = payload.get("id")
                    # node_info.long_name = payload.get("longname", None) # 解析 emoji 會有問題
                    # node_info.short_name = payload.get("shortname", None) # 解析 emoji 會有問題
                    if payload.get("hardware", None) is not None:
                        node_info.hw_model = payload.get("hardware")
                    if payload.get("role", None) is not None:
                        node_info.role = payload.get("role")
                    data = json.loads(
                        MessageToJson(
                            node_info,
                            preserving_proto_field_name=True,
                            ensure_ascii=False,
                        )
                    )
                    message_json["payload"] = data
            elif "/2/e/" in topic or "/2/map" in topic:
                mp = mesh_pb2.MeshPacket()
                try:
                    se = mqtt_pb2.ServiceEnvelope()
                    se.ParseFromString(message.payload)
                    mp = se.packet
                except Exception as _:
                    pass

                # 檢查是否為加密封包
                if mp.HasField("encrypted") and not mp.HasField("decoded"):
                    mp = self.decode_encrypted(topic, mp)
                    if mp is None:
                        return
                message_json["id"] = getattr(mp, "id")
                message_json["channel"] = getattr(mp, "channel")
                message_json["from"] = getattr(mp, "from")
                message_json["payload"] = {}
                message_json["sender"] = (
                    f"!{MeshtasticUtil.convert_node_id_from_int_to_hex(getattr(mp, 'from'))}"
                )
                message_json["timestamp"] = mp.rx_time
                message_json["to"] = getattr(mp, "to")
                message_json["type"] = "unknown"
                message_json["topic"] = topic
                # meshtastic protobuf 定義 https://github.com/meshtastic/protobufs
                if mp.decoded.portnum == portnums_pb2.MAP_REPORT_APP:
                    mapreport = mqtt_pb2.MapReport()
                    mapreport.ParseFromString(mp.decoded.payload)
                    data = json.loads(
                        MessageToJson(
                            mapreport,
                            preserving_proto_field_name=True,
                            ensure_ascii=False,
                        )
                    )
                    message_json["type"] = "mapreport"
                    message_json["payload"] = data
                elif mp.decoded.portnum == portnums_pb2.NEIGHBORINFO_APP:
                    neighbor_info = mesh_pb2.NeighborInfo()
                    neighbor_info.ParseFromString(mp.decoded.payload)
                    data = json.loads(
                        MessageToJson(
                            neighbor_info,
                            preserving_proto_field_name=True,
                            ensure_ascii=False,
                        )
                    )
                    message_json["type"] = "neighborinfo"
                    message_json["payload"] = data
                elif mp.decoded.portnum == portnums_pb2.NODEINFO_APP:
                    node_info = mesh_pb2.User()
                    node_info.ParseFromString(mp.decoded.payload)
                    data = json.loads(
                        MessageToJson(
                            node_info,
                            preserving_proto_field_name=True,
                            ensure_ascii=False,
                        )
                    )
                    message_json["type"] = "nodeinfo"
                    message_json["payload"] = data
                elif mp.decoded.portnum == portnums_pb2.POSITION_APP:
                    position = mesh_pb2.Position()
                    position.ParseFromString(mp.decoded.payload)
                    data = json.loads(
                        MessageToJson(position, preserving_proto_field_name=True)
                    )
                    message_json["type"] = "position"
                    message_json["payload"] = data
                elif mp.decoded.portnum == portnums_pb2.TELEMETRY_APP:
                    telemetry = telemetry_pb2.Telemetry()
                    telemetry.ParseFromString(mp.decoded.payload)
                    data = json.loads(
                        MessageToJson(
                            telemetry,
                            preserving_proto_field_name=True,
                            ensure_ascii=False,
                        )
                    )
                    message_json["type"] = "telemetry"
                    message_json["payload"] = data
                else:
                    message_json["type"] = f"unknown({mp.decoded.portnum})"
                    message_json["payload"] = {}

            # print(f"message_json: {message_json}")
            if "type" not in message_json:
                return

            # 更新最後聽到的時間
            if not await self.check_node_exist(message_json.get("from")):
                await self.create_node(
                    Node(
                        id=message_json.get("from"),
                        last_heard_at=datetime.now(timezone.utc),
                    )
                )
            else:
                await self.update_node_last_heard_at(message_json.get("from"))

            # 確保訊息內容
            # 時間為 None 或是 0 時，將時間設為當下
            if "timestamp" not in message_json or message_json["timestamp"] == 0:
                message_json["timestamp"] = datetime.now(timezone.utc).timestamp()

            # 如果時間來自未來，則跳過
            if datetime.fromtimestamp(
                message_json["timestamp"], tz=timezone.utc
            ) > datetime.now(timezone.utc):
                return

            # 開始處理
            if message_json["type"] == "mapreport":
                await self.handle_mapreport_app(message_json)
            elif message_json["type"] == "neighborinfo":
                await self.handle_neighborinfo_app(message_json)
            elif message_json["type"] == "nodeinfo":
                await self.handle_nodeinfo_app(message_json)
            elif message_json["type"] == "position":
                await self.handle_position_app(message_json)
            elif message_json["type"] == "telemetry":
                await self.handle_telemetry_app(message_json)
            else:
                # print(f"未定義處理: {message_json['type']} \n{message_json}")
                return
            pass
        except Exception as e:
            self.logger.error(f"{inspect.currentframe().f_code.co_name}: {e}")
            return

    def decode_encrypted(self, topic: str, mp):
        public_key = "1PG7OiApB1nwvP+rz05pAQ=="
        try:
            # 讀取解密金鑰
            key_list = ConfigUtil().get_config("meshtastic.channels", [])
            # 解析 topic 獲取 channel
            channel = topic.split("/")[-2]
            # 取得 channel 對應的金鑰
            key = next(
                (item["key"] for item in key_list if item["name"] == channel), None
            )
            if key is None:
                self.logger.debug(f"找不到 '{channel}' 的金鑰，使用公開金鑰 '{public_key}' 嘗試解密")
                key = public_key
            # 轉換金鑰為 base64
            key_bytes = base64.b64decode(key.encode("ascii"))

            # 隨機數
            nonce_packet_id = getattr(mp, "id").to_bytes(8, "little")
            nonce_from_node = getattr(mp, "from").to_bytes(8, "little")
            nonce = nonce_packet_id + nonce_from_node

            # 建立解密器
            cipher = Cipher(
                algorithms.AES(key_bytes),
                modes.CTR(nonce),
                backend=default_backend(),
            )
            decryptor = cipher.decryptor()
            decrypted_bytes = (
                decryptor.update(getattr(mp, "encrypted")) + decryptor.finalize()
            )

            data = mesh_pb2.Data()
            data.ParseFromString(decrypted_bytes)
            mp.decoded.CopyFrom(data)  
            # 回傳解密後的封包
            return mp
        except Exception as e:
            self.logger.debug(f"解密失敗: {e}")
            return None

    #################################
    # 事件處理
    #################################

    async def handle_mapreport_app(self, message_json: dict):
        try:
            # TODO: 尚未被廣泛使用，待確認
            payload = message_json.get("payload")
            now = datetime.now(timezone.utc).replace(microsecond=0)
            firmware_version = payload.get("firmware_version")

            # 來自這裡的提示: https://github.com/brianshea2/meshmap.net/blob/da626616b2fb1f52999d24d1b63c7f59af391f92/cmd/meshobserv/meshobserv.go#L136
            if not firmware_version or firmware_version.startswith("2.3.1."):
                print(f"跳過 {message_json.get('from')} 的 mapreport \n{message_json}")
                return

            # 新增 NodeInfo
            node_info = await self.create_or_update_node_info(
                NodeInfo(
                    node_id=message_json.get("from"),
                    long_name=payload.get("long_name", None),
                    short_name=payload.get("short_name", None),
                    role=payload.get("role", None),
                    hw_model=(
                        payload.get("hw_model", None)
                        if isinstance(payload.get("hw_model"), str)
                        else None
                    ),
                    firmware_version=firmware_version,
                    lora_region=payload.get("region", None),
                    lora_modem_preset=payload.get("modem_preset", None),
                    has_default_channel=payload.get("has_default_channel", None),
                    num_online_local_nodes=payload.get("num_online_local_nodes", None),
                    update_at=now,
                    topic=message_json.get("topic"),
                )
            )
            # 新增 NodePosition
            if "latitude_i" in payload and "longitude_i" in payload:
                # 轉換經緯度
                latitude = payload.get("latitude_i") / 1e7
                longitude = payload.get("longitude_i") / 1e7

                # 如果經緯度不合法，則跳過
                if not (
                    isinstance(latitude, numbers.Number)
                    and isinstance(longitude, numbers.Number)
                    and -90 <= latitude <= 90
                    and -180 <= longitude <= 180
                ):
                    return

                # 如果在 0 度線上，則跳過
                if latitude == 0 and longitude == 0:
                    return

                node_position = await self.create_or_update_node_position(
                    NodePosition(
                        node_id=message_json.get("from"),
                        latitude=latitude,
                        longitude=longitude,
                        altitude=payload.get("altitude", None),
                        precision_bits=payload.get("position_precision", None),
                        create_at=now.replace(
                            minute=0, second=0, microsecond=0
                        ),  # 將時間精確度調整到小時
                        update_at=now,
                        topic=message_json.get("topic"),
                    )
                )
            pass
        except Exception as e:
            self.logger.error(f"{inspect.currentframe().f_code.co_name}: {e}")
            raise e

    async def handle_neighborinfo_app(self, message_json: dict):
        try:
            payload = message_json.get("payload")

            # 新增 NodeNeighborInfo
            node_neighbor_info = await self.create_or_update_node_neighbor_info(
                NodeNeighborInfo(
                    node_id=payload.get("node_id"),
                    last_sent_by_id=payload.get("last_sent_by_id"),
                    node_broadcast_interval_secs=payload.get(
                        "node_broadcast_interval_secs"
                    ),
                    update_at=datetime.fromtimestamp(
                        message_json.get("timestamp"), tz=timezone.utc
                    ),
                    topic=message_json.get("topic"),
                )
            )
            # 新增 NodeNeighborEdge
            node_neighbor_edges = []
            for edge in payload.get("neighbors", []):
                node_neighbor_edges.append(
                    NodeNeighborEdge(
                        node_id=node_neighbor_info.node_id,
                        edge_node_id=edge.get("node_id"),
                        snr=edge.get("snr", None),
                    )
                )
            if len(node_neighbor_edges) > 0:
                # 清空 NodeNeighborEdge
                await self.clear_node_neighbor_edges(node_neighbor_info.node_id)
                # 新增 NodeNeighborEdge
                node_neighbor_edges = await self.create_node_neighbor_edges(
                    node_neighbor_edges
                )
        except Exception as e:
            self.logger.error(f"{inspect.currentframe().f_code.co_name}: {e}")
            raise e

    async def handle_nodeinfo_app(self, message_json: dict):
        try:
            payload = message_json.get("payload")

            if (
                "id" not in payload
                or "long_name" not in payload
                or "short_name" not in payload
            ):
                return
            node_id = MeshtasticUtil.convert_node_id_from_hex_to_int(payload.get("id"))
            # 新增 NodeInfo
            node_info = await self.create_or_update_node_info(
                NodeInfo(
                    node_id=node_id,
                    long_name=payload.get("long_name"),
                    short_name=payload.get("short_name"),
                    hw_model=(
                        payload.get("hw_model", None)
                        if isinstance(payload.get("hw_model"), str)
                        else None
                    ),
                    is_licensed=payload.get("is_licensed", None),
                    role=payload.get("role", None),
                    update_at=datetime.fromtimestamp(
                        message_json.get("timestamp"), tz=timezone.utc
                    ).replace(microsecond=0),
                    topic=message_json.get("topic"),
                )
            )
        except Exception as e:
            self.logger.error(f"{inspect.currentframe().f_code.co_name}: {e}")
            raise e

    async def handle_position_app(self, message_json: dict):
        try:
            payload = message_json.get("payload")

            if "latitude_i" not in payload or "longitude_i" not in payload:
                return

            # 轉換經緯度
            latitude = payload.get("latitude_i") / 1e7
            longitude = payload.get("longitude_i") / 1e7

            # 如果經緯度不合法，則跳過
            if not (
                isinstance(latitude, numbers.Number)
                and isinstance(longitude, numbers.Number)
                and -90 <= latitude <= 90
                and -180 <= longitude <= 180
            ):
                return

            # 如果在 0 度線上，則跳過
            if latitude == 0 and longitude == 0:
                return

            # 新增 NodePosition
            node_position = await self.create_or_update_node_position(
                NodePosition(
                    node_id=message_json.get("from"),
                    latitude=latitude,
                    longitude=longitude,
                    altitude=payload.get("altitude", None),
                    precision_bits=payload.get("precision_bits", None),
                    sats_in_view=payload.get("sats_in_view", None),
                    create_at=datetime.fromtimestamp(
                        message_json.get("timestamp"), tz=timezone.utc
                    ).replace(
                        minute=0, second=0, microsecond=0
                    ),  # 將時間精確度調整到小時
                    update_at=datetime.fromtimestamp(
                        message_json.get("timestamp"), tz=timezone.utc
                    ),
                    topic=message_json.get("topic"),
                )
            )
        except Exception as e:
            self.logger.error(f"{inspect.currentframe().f_code.co_name}: {e}")
            raise e

    async def handle_telemetry_app(self, message_json: dict):
        try:
            payload = message_json.get("payload")

            if "time" not in payload:
                return

            if datetime.fromtimestamp(payload.get("time")) > datetime.now():
                payload["time"] = datetime.now().timestamp()

            air_quality_metrics = payload.get("air_quality_metrics", None)
            if air_quality_metrics:
                node_telemetry_air_quality = (
                    await self.create_or_update_node_telemetry_air_quality(
                        NodeTelemetryAirQuality(
                            node_id=message_json.get("from"),
                            pm10_standard=self.get_telemetry_value_or_none(
                                air_quality_metrics, "pm10_standard"
                            ),
                            pm25_standard=self.get_telemetry_value_or_none(
                                air_quality_metrics, "pm25_standard"
                            ),
                            pm100_standard=self.get_telemetry_value_or_none(
                                air_quality_metrics, "pm100_standard"
                            ),
                            pm10_environmental=self.get_telemetry_value_or_none(
                                air_quality_metrics, "pm10_environmental"
                            ),
                            pm25_environmental=self.get_telemetry_value_or_none(
                                air_quality_metrics, "pm25_environmental"
                            ),
                            pm100_environmental=self.get_telemetry_value_or_none(
                                air_quality_metrics, "pm100_environmental"
                            ),
                            particles_03um=self.get_telemetry_value_or_none(
                                air_quality_metrics, "particles_03um"
                            ),
                            particles_05um=self.get_telemetry_value_or_none(
                                air_quality_metrics, "particles_05um"
                            ),
                            particles_10um=self.get_telemetry_value_or_none(
                                air_quality_metrics, "particles_10um"
                            ),
                            particles_25um=self.get_telemetry_value_or_none(
                                air_quality_metrics, "particles_25um"
                            ),
                            particles_50um=self.get_telemetry_value_or_none(
                                air_quality_metrics, "particles_50um"
                            ),
                            particles_100um=self.get_telemetry_value_or_none(
                                air_quality_metrics, "particles_100um"
                            ),
                            create_at=datetime.fromtimestamp(
                                payload.get("time"), tz=timezone.utc
                            ).replace(
                                minute=0, second=0, microsecond=0
                            ),  # 將時間精確度調整到小時
                            update_at=datetime.fromtimestamp(
                                payload.get("time"), tz=timezone.utc
                            ),
                            topic=message_json.get("topic"),
                        )
                    )
                )
            device_metrics = payload.get("device_metrics", None)
            if device_metrics:
                # 新增 NodeTelemetryDevice
                node_telemetry_device = (
                    await self.create_or_update_node_telemetry_device(
                        NodeTelemetryDevice(
                            node_id=message_json.get("from"),
                            battery_level=device_metrics.get("battery_level", None),
                            voltage=device_metrics.get("voltage", None),
                            channel_utilization=device_metrics.get(
                                "channel_utilization", None
                            ),
                            air_util_tx=device_metrics.get("air_util_tx", None),
                            uptime_seconds=device_metrics.get("uptime_seconds", None),
                            create_at=datetime.fromtimestamp(
                                payload.get("time"), tz=timezone.utc
                            ).replace(
                                minute=0, second=0, microsecond=0
                            ),  # 將時間精確度調整到小時
                            update_at=datetime.fromtimestamp(
                                payload.get("time"), tz=timezone.utc
                            ),
                            topic=message_json.get("topic"),
                        )
                    )
                )

            environment_metrics = payload.get("environment_metrics", None)
            if environment_metrics:
                node_telemetry_environment = (
                    await self.create_or_update_node_telemetry_environment(
                        NodeTelemetryEnvironment(
                            node_id=message_json.get("from"),
                            temperature=self.get_telemetry_value_or_none(
                                environment_metrics, "temperature"
                            ),
                            relative_humidity=self.get_telemetry_value_or_none(
                                environment_metrics, "relative_humidity"
                            ),
                            barometric_pressure=environment_metrics.get(
                                "barometric_pressure", None
                            ),
                            gas_resistance=environment_metrics.get(
                                "gas_resistance", None
                            ),
                            voltage=environment_metrics.get("voltage", None),
                            current=environment_metrics.get("current", None),
                            iaq=environment_metrics.get("iaq", None),
                            distance=environment_metrics.get("distance", None),
                            lux=self.get_telemetry_value_or_none(
                                environment_metrics, "lux"
                            ),
                            white_lux=self.get_telemetry_value_or_none(
                                environment_metrics, "white_lux"
                            ),
                            ir_lux=self.get_telemetry_value_or_none(
                                environment_metrics, "ir_lux"
                            ),
                            uv_lux=self.get_telemetry_value_or_none(
                                environment_metrics, "uv_lux"
                            ),
                            wind_direction=environment_metrics.get(
                                "wind_direction", None
                            ),
                            wind_speed=environment_metrics.get("wind_speed", None),
                            weight=environment_metrics.get("weight", None),
                            wind_gust=environment_metrics.get("wind_gust", None),
                            wind_lull=environment_metrics.get("wind_lull", None),
                            create_at=datetime.fromtimestamp(
                                payload.get("time"), tz=timezone.utc
                            ).replace(
                                minute=0, second=0, microsecond=0
                            ),  # 將時間精確度調整到小時
                            update_at=datetime.fromtimestamp(
                                payload.get("time"), tz=timezone.utc
                            ),
                            topic=message_json.get("topic"),
                        )
                    )
                )
            power_metrics = payload.get("power_metrics", None)
            if power_metrics:
                node_telemetry_power = await self.create_or_update_node_telemetry_power(
                    NodeTelemetryPower(
                        node_id=message_json.get("from"),
                        ch1_voltage=power_metrics.get("ch1_voltage", None),
                        ch1_current=power_metrics.get("ch1_current", None),
                        ch2_voltage=power_metrics.get("ch2_voltage", None),
                        ch2_current=power_metrics.get("ch2_current", None),
                        ch3_voltage=power_metrics.get("ch3_voltage", None),
                        ch3_current=power_metrics.get("ch3_current", None),
                        create_at=datetime.fromtimestamp(
                            payload.get("time"), tz=timezone.utc
                        ).replace(
                            minute=0, second=0, microsecond=0
                        ),  # 將時間精確度調整到小時
                        update_at=datetime.fromtimestamp(
                            payload.get("time"), tz=timezone.utc
                        ),
                        topic=message_json.get("topic"),
                    )
                )

        except Exception as e:
            self.logger.error(f"{inspect.currentframe().f_code.co_name}: {e}")

    #################################
    # 資料庫操作
    #################################

    # 檢查 Node 是否已存在
    async def check_node_exist(self, id: int) -> bool:
        async for session in get_db_connection_async():
            try:
                result = await session.execute(select(Node).where(Node.id == id))
                return result.scalar() is not None
            except Exception as e:
                await session.rollback()
                raise e
            finally:
                await session.close()

    # 新增 Node
    async def create_node(self, node: Node):
        async for session in get_db_connection_async():
            try:
                node = Node(
                    id=node.id,
                    id_hex=(
                        node.id_hex
                        if node.id_hex is not None
                        else MeshtasticUtil.convert_node_id_from_int_to_hex(node.id)
                    ),
                    last_heard_at=node.last_heard_at,
                )
                session.add(node)
                await session.commit()
            except Exception as e:
                await session.rollback()
                raise e
            finally:
                await session.close()

    # 更新 Node
    async def update_node_last_heard_at(self, id: int):
        async for session in get_db_connection_async():
            try:
                await session.execute(
                    update(Node)
                    .where(Node.id == id)
                    .values(last_heard_at=datetime.now(timezone.utc))
                )
                await session.commit()
            except Exception as e:
                await session.rollback()
                raise e
            finally:
                await session.close()

    # 新增或更新 NodeInfo
    async def create_or_update_node_info(self, node_info: NodeInfo) -> NodeInfo:
        async for session in get_db_connection_async():
            try:
                # 一些傳入資料型態的檢查
                if not isinstance(node_info.role, str):
                    node_info.role = None
                # 檢查 Node 是否存在
                if not await self.check_node_exist(node_info.node_id):
                    await self.create_node(
                        Node(id=node_info.node_id, last_heard_at=node_info.update_at)
                    )
                # 檢查 NodeInfo 是否存在
                result = await session.execute(
                    select(NodeInfo).where(NodeInfo.node_id == node_info.node_id)
                )
                existing_node_info = result.scalar()
                # 如果 NodeInfo 不存在，則新增
                if existing_node_info is None:
                    session.add(node_info)
                    await session.commit()
                    await session.refresh(node_info)
                    return node_info
                # 如果 NodeInfo 存在，但傳入比較舊，則直接回傳
                if node_info.update_at < existing_node_info.update_at:
                    return existing_node_info
                # 更新 NodeInfo
                await session.execute(
                    update(NodeInfo)
                    .where(NodeInfo.node_id == node_info.node_id)
                    .values(
                        long_name=(
                            node_info.long_name
                            if node_info.long_name is not None
                            else existing_node_info.long_name
                        ),
                        short_name=(
                            node_info.short_name
                            if node_info.short_name is not None
                            else existing_node_info.short_name
                        ),
                        hw_model=(
                            node_info.hw_model
                            if node_info.hw_model is not None
                            else existing_node_info.hw_model
                        ),
                        is_licensed=(
                            node_info.is_licensed
                            if node_info.is_licensed is not None
                            else existing_node_info.is_licensed
                        ),
                        role=(
                            node_info.role
                            if node_info.role is not None
                            else existing_node_info.role
                        ),
                        firmware_version=(
                            node_info.firmware_version
                            if node_info.firmware_version is not None
                            else existing_node_info.firmware_version
                        ),
                        lora_region=(
                            node_info.lora_region
                            if node_info.lora_region is not None
                            else existing_node_info.lora_region
                        ),
                        lora_modem_preset=(
                            node_info.lora_modem_preset
                            if node_info.lora_modem_preset is not None
                            else existing_node_info.lora_modem_preset
                        ),
                        has_default_channel=(
                            node_info.has_default_channel
                            if node_info.has_default_channel is not None
                            else existing_node_info.has_default_channel
                        ),
                        num_online_local_nodes=(
                            node_info.num_online_local_nodes
                            if node_info.num_online_local_nodes is not None
                            else existing_node_info.num_online_local_nodes
                        ),
                        update_at=node_info.update_at,
                        topic=node_info.topic,
                    )
                )
                await session.commit()
                await session.refresh(existing_node_info)
                return existing_node_info
            except Exception as e:
                await session.rollback()
                raise e
            finally:
                await session.close()

    # 清空 NodeNeighborEdge
    async def clear_node_neighbor_edges(self, node_id: int) -> None:
        async for session in get_db_connection_async():
            try:
                # 清空 NodeNeighborEdge
                await session.execute(
                    delete(NodeNeighborEdge).where(NodeNeighborEdge.node_id == node_id)
                )
                await session.commit()
            except Exception as e:
                await session.rollback()
                raise e
            finally:
                await session.close()

    # 新增 NodeNeighborEdge
    async def create_node_neighbor_edges(
        self, node_neighbor_edges: list[NodeNeighborEdge]
    ) -> list[NodeNeighborEdge]:
        async for session in get_db_connection_async():
            try:
                # 檢查 list[NodeNeighborEdge] 中各個 edge_node_id  是否存在
                for node_neighbor_edge in node_neighbor_edges:
                    if not await self.check_node_exist(node_neighbor_edge.edge_node_id):
                        await self.create_node(
                            Node(
                                id=node_neighbor_edge.edge_node_id,
                            )
                        )
                # 新增 NodeNeighborEdge
                session.add_all(node_neighbor_edges)
                await session.commit()
                return node_neighbor_edges
            except Exception as e:
                await session.rollback()
                raise e
            finally:
                await session.close()

    # 新增或更新 NodeNeighborInfo
    async def create_or_update_node_neighbor_info(
        self, node_neighbor_info: NodeNeighborInfo
    ) -> NodeNeighborInfo:
        async for session in get_db_connection_async():
            try:
                # 檢查 node_neighbor_info.node_id 是否存在
                if not await self.check_node_exist(node_neighbor_info.node_id):
                    await self.create_node(
                        Node(
                            id=node_neighbor_info.node_id,
                            last_heard_at=node_neighbor_info.update_at,
                        )
                    )

                # 檢查 node_neighbor_info.last_sent_by_id 是否存在
                if not await self.check_node_exist(node_neighbor_info.last_sent_by_id):
                    await self.create_node(
                        Node(
                            id=node_neighbor_info.last_sent_by_id,
                            last_heard_at=node_neighbor_info.update_at,
                        )
                    )

                # 檢查 NodeNeighborInfo 是否存在
                existing_node_neighbor_info = (
                    await session.execute(
                        select(NodeNeighborInfo).where(
                            NodeNeighborInfo.node_id == node_neighbor_info.node_id
                        )
                    )
                ).scalar()

                # 如果 NodeNeighborInfo 存在，但傳入比較舊，則直接回傳
                if (
                    existing_node_neighbor_info is not None
                    and node_neighbor_info.update_at
                    < existing_node_neighbor_info.update_at
                ):
                    return existing_node_neighbor_info

                # 動態構建 set_ 字典，移除值為 None 的鍵
                data = {
                    "last_sent_by_id": node_neighbor_info.last_sent_by_id,
                    "node_broadcast_interval_secs": node_neighbor_info.node_broadcast_interval_secs,
                    "update_at": node_neighbor_info.update_at,
                    "topic": node_neighbor_info.topic,
                }
                data = {k: v for k, v in data.items() if v is not None}

                # 使用 ON CONFLICT 子句來新增或更新
                stmt = (
                    insert(NodeNeighborInfo)
                    .values(
                        node_id=node_neighbor_info.node_id,
                        **data,
                    )
                    .on_conflict_do_update(
                        index_elements=["node_id"],
                        set_=data,
                    )
                )
                await session.execute(stmt)
                await session.commit()
                finanl_node_neighbor_info = (
                    await session.execute(
                        select(NodeNeighborInfo).where(
                            NodeNeighborInfo.node_id == node_neighbor_info.node_id
                        )
                    )
                ).scalar()
                return finanl_node_neighbor_info
            except Exception as e:
                await session.rollback()
                raise e
            finally:
                await session.close()

    # 新增或更新 NodePosition
    async def create_or_update_node_position(
        self, node_position: NodePosition
    ) -> NodePosition:
        # 檢查精度是否符合限制，如果沒有則進行模糊處理
        if (
            node_position.precision_bits is None
            or node_position.precision_bits
            > self.config["meshtastic"]["position"]["maxPrecisionBits"]
        ):
            (node_position.latitude, node_position.longitude) = (
                MeshtasticUtil.blur_position(
                    node_position.latitude,
                    node_position.longitude,
                    MeshtasticUtil.convert_precision_to_meter(
                        self.config["meshtastic"]["position"]["maxPrecisionBits"]
                    ),
                )
            )
            node_position.precision_bits = self.config["meshtastic"]["position"][
                "maxPrecisionBits"
            ]

        async for session in get_db_connection_async():
            try:
                # 檢查 Node 是否存在
                if not await self.check_node_exist(node_position.node_id):
                    await self.create_node(
                        Node(
                            id=node_position.node_id,
                            last_heard_at=node_position.update_at,
                        )
                    )

                # 檢查 NodePosition 是否存在
                existing_node_position = (
                    await session.execute(
                        select(NodePosition)
                        .where(NodePosition.node_id == node_position.node_id)
                        .where(NodePosition.create_at == node_position.create_at)
                        .where(NodePosition.topic == node_position.topic)
                    )
                ).scalar()

                # 如果 NodePosition 存在，但傳入比較舊，則直接回傳
                if (
                    existing_node_position is not None
                    and node_position.update_at < existing_node_position.update_at
                ):
                    return existing_node_position

                # 動態構建 set_ 字典，移除值為 None 的鍵
                data = {
                    "latitude": node_position.latitude,
                    "longitude": node_position.longitude,
                    "altitude": node_position.altitude,
                    "precision_bits": node_position.precision_bits,
                    "sats_in_view": node_position.sats_in_view,
                    "update_at": node_position.update_at,
                }
                data = {k: v for k, v in data.items() if v is not None}

                # 使用 ON CONFLICT 子句來新增或更新
                stmt = (
                    insert(NodePosition)
                    .values(
                        node_id=node_position.node_id,
                        create_at=node_position.create_at,
                        topic=node_position.topic,
                        **data,
                    )
                    .on_conflict_do_update(
                        index_elements=["node_id", "create_at", "topic"],
                        set_=data,
                    )
                )
                await session.execute(stmt)
                await session.commit()
                final_node_position = (
                    await session.execute(
                        select(NodePosition)
                        .where(NodePosition.node_id == node_position.node_id)
                        .where(NodePosition.create_at == node_position.create_at)
                        .where(NodePosition.topic == node_position.topic)
                    )
                ).scalar()
                return final_node_position
            except Exception as e:
                await session.rollback()
                raise e
            finally:
                await session.close()

    # 新增或更新 NodeTelemetryAirQuality
    async def create_or_update_node_telemetry_air_quality(
        self, node_telemetry_air_quality: NodeTelemetryAirQuality
    ) -> NodeTelemetryAirQuality:
        async for session in get_db_connection_async():
            try:
                # 檢查 Node 是否存在
                if not await self.check_node_exist(node_telemetry_air_quality.node_id):
                    await self.create_node(
                        Node(
                            id=node_telemetry_air_quality.node_id,
                            last_heard_at=node_telemetry_air_quality.update_at,
                        )
                    )

                # 檢查 NodeTelemetryAirQuality 是否存在
                existing_node_telemetry_air_quality = (
                    await session.execute(
                        select(NodeTelemetryAirQuality)
                        .where(
                            NodeTelemetryAirQuality.node_id
                            == node_telemetry_air_quality.node_id
                        )
                        .where(
                            NodeTelemetryAirQuality.create_at
                            == node_telemetry_air_quality.create_at
                        )
                    )
                ).scalar()

                # 如果 NodeTelemetryAirQuality 存在，但傳入比較舊，則直接回傳
                if (
                    existing_node_telemetry_air_quality is not None
                    and node_telemetry_air_quality.update_at
                    < existing_node_telemetry_air_quality.update_at
                ):
                    return existing_node_telemetry_air_quality

                # 動態構建 set_ 字典，移除值為 None 的鍵
                data = {
                    "pm10_standard": node_telemetry_air_quality.pm10_standard,
                    "pm25_standard": node_telemetry_air_quality.pm25_standard,
                    "pm100_standard": node_telemetry_air_quality.pm100_standard,
                    "pm10_environmental": node_telemetry_air_quality.pm10_environmental,
                    "pm25_environmental": node_telemetry_air_quality.pm25_environmental,
                    "pm100_environmental": node_telemetry_air_quality.pm100_environmental,
                    "particles_03um": node_telemetry_air_quality.particles_03um,
                    "particles_05um": node_telemetry_air_quality.particles_05um,
                    "particles_10um": node_telemetry_air_quality.particles_10um,
                    "particles_25um": node_telemetry_air_quality.particles_25um,
                    "particles_50um": node_telemetry_air_quality.particles_50um,
                    "particles_100um": node_telemetry_air_quality.particles_100um,
                    "update_at": node_telemetry_air_quality.update_at,
                    "topic": node_telemetry_air_quality.topic,
                }
                data = {k: v for k, v in data.items() if v is not None}

                # 使用 ON CONFLICT 子句來新增或更新
                stmt = (
                    insert(NodeTelemetryAirQuality)
                    .values(
                        node_id=node_telemetry_air_quality.node_id,
                        create_at=node_telemetry_air_quality.create_at,
                        **data,
                    )
                    .on_conflict_do_update(
                        index_elements=["node_id", "create_at"],
                        set_=data,
                    )
                )
                await session.execute(stmt)
                await session.commit()
                final_node_telemetry_air_quality = (
                    await session.execute(
                        select(NodeTelemetryAirQuality)
                        .where(
                            NodeTelemetryAirQuality.node_id
                            == node_telemetry_air_quality.node_id
                        )
                        .where(
                            NodeTelemetryAirQuality.create_at
                            == node_telemetry_air_quality.create_at
                        )
                    )
                ).scalar()
                return final_node_telemetry_air_quality
            except Exception as e:
                await session.rollback()
                raise e
            finally:
                await session.close()

    # 新增或更新 NodeTelemetryDevice
    async def create_or_update_node_telemetry_device(
        self, node_telemetry_device: NodeTelemetryDevice
    ) -> NodeTelemetryDevice:
        async for session in get_db_connection_async():
            try:
                # 檢查 Node 是否存在
                if not await self.check_node_exist(node_telemetry_device.node_id):
                    await self.create_node(
                        Node(
                            id=node_telemetry_device.node_id,
                            last_heard_at=node_telemetry_device.update_at,
                        )
                    )

                # 檢查 NodeTelemetryDevice 是否存在
                existing_node_telemetry_device = (
                    await session.execute(
                        select(NodeTelemetryDevice)
                        .where(
                            NodeTelemetryDevice.node_id == node_telemetry_device.node_id
                        )
                        .where(
                            NodeTelemetryDevice.create_at
                            == node_telemetry_device.create_at
                        )
                    )
                ).scalar()

                # 如果 NodeTelemetryDevice 存在，但傳入比較舊，則直接回傳
                if (
                    existing_node_telemetry_device is not None
                    and node_telemetry_device.update_at
                    < existing_node_telemetry_device.update_at
                ):
                    return existing_node_telemetry_device

                # 動態構建 set_ 字典，移除值為 None 的鍵
                data = {
                    "battery_level": node_telemetry_device.battery_level,
                    "voltage": node_telemetry_device.voltage,
                    "channel_utilization": node_telemetry_device.channel_utilization,
                    "air_util_tx": node_telemetry_device.air_util_tx,
                    "uptime_seconds": node_telemetry_device.uptime_seconds,
                    "update_at": node_telemetry_device.update_at,
                    "topic": node_telemetry_device.topic,
                }
                data = {k: v for k, v in data.items() if v is not None}

                # 使用 ON CONFLICT 子句來新增或更新
                stmt = (
                    insert(NodeTelemetryDevice)
                    .values(
                        node_id=node_telemetry_device.node_id,
                        create_at=node_telemetry_device.create_at,
                        **data,
                    )
                    .on_conflict_do_update(
                        index_elements=["node_id", "create_at"],
                        set_=data,
                    )
                )
                await session.execute(stmt)
                await session.commit()
                final_node_telemetry_device = (
                    await session.execute(
                        select(NodeTelemetryDevice)
                        .where(
                            NodeTelemetryDevice.node_id == node_telemetry_device.node_id
                        )
                        .where(
                            NodeTelemetryDevice.create_at
                            == node_telemetry_device.create_at
                        )
                    )
                ).scalar()
                return final_node_telemetry_device
            except Exception as e:
                await session.rollback()
                raise e
            finally:
                await session.close()

    # 新增或更新 NodeTelemetryEnvironment
    async def create_or_update_node_telemetry_environment(
        self, node_telemetry_environment: NodeTelemetryEnvironment
    ) -> NodeTelemetryEnvironment:
        async for session in get_db_connection_async():
            try:
                # 檢查 Node 是否存在
                if not await self.check_node_exist(node_telemetry_environment.node_id):
                    await self.create_node(
                        Node(
                            id=node_telemetry_environment.node_id,
                            last_heard_at=node_telemetry_environment.update_at,
                        )
                    )

                # 檢查 NodeTelemetryEnvironment 是否存在
                existing_node_telemetry_environment = (
                    await session.execute(
                        select(NodeTelemetryEnvironment)
                        .where(
                            NodeTelemetryEnvironment.node_id
                            == node_telemetry_environment.node_id
                        )
                        .where(
                            NodeTelemetryEnvironment.create_at
                            == node_telemetry_environment.create_at
                        )
                    )
                ).scalar()

                # 如果 NodeTelemetryEnvironment 存在，但傳入比較舊，則直接回傳
                if (
                    existing_node_telemetry_environment is not None
                    and node_telemetry_environment.update_at
                    < existing_node_telemetry_environment.update_at
                ):
                    return existing_node_telemetry_environment

                # 動態構建 set_ 字典，移除值為 None 的鍵
                data = {
                    "temperature": node_telemetry_environment.temperature,
                    "relative_humidity": node_telemetry_environment.relative_humidity,
                    "barometric_pressure": node_telemetry_environment.barometric_pressure,
                    "gas_resistance": node_telemetry_environment.gas_resistance,
                    "voltage": node_telemetry_environment.voltage,
                    "current": node_telemetry_environment.current,
                    "iaq": node_telemetry_environment.iaq,
                    "distance": node_telemetry_environment.distance,
                    "lux": node_telemetry_environment.lux,
                    "white_lux": node_telemetry_environment.white_lux,
                    "ir_lux": node_telemetry_environment.ir_lux,
                    "uv_lux": node_telemetry_environment.uv_lux,
                    "wind_direction": node_telemetry_environment.wind_direction,
                    "wind_speed": node_telemetry_environment.wind_speed,
                    "weight": node_telemetry_environment.weight,
                    "wind_gust": node_telemetry_environment.wind_gust,
                    "wind_lull": node_telemetry_environment.wind_lull,
                    "update_at": node_telemetry_environment.update_at,
                    "topic": node_telemetry_environment.topic,
                }
                data = {k: v for k, v in data.items() if v is not None}

                # 使用 ON CONFLICT 子句來新增或更新
                stmt = (
                    insert(NodeTelemetryEnvironment)
                    .values(
                        node_id=node_telemetry_environment.node_id,
                        create_at=node_telemetry_environment.create_at,
                        **data,
                    )
                    .on_conflict_do_update(
                        index_elements=["node_id", "create_at"],
                        set_=data,
                    )
                )
                await session.execute(stmt)
                await session.commit()
                final_node_telemetry_environment = (
                    await session.execute(
                        select(NodeTelemetryEnvironment)
                        .where(
                            NodeTelemetryEnvironment.node_id
                            == node_telemetry_environment.node_id
                        )
                        .where(
                            NodeTelemetryEnvironment.create_at
                            == node_telemetry_environment.create_at
                        )
                    )
                ).scalar()
                return final_node_telemetry_environment
            except Exception as e:
                await session.rollback()
                raise e
            finally:
                await session.close()

    # 新增或更新 NodeTelemetryPower
    async def create_or_update_node_telemetry_power(
        self, node_telemetry_power: NodeTelemetryPower
    ) -> NodeTelemetryPower:
        async for session in get_db_connection_async():
            try:
                # 檢查 Node 是否存在
                if not await self.check_node_exist(node_telemetry_power.node_id):
                    await self.create_node(
                        Node(
                            id=node_telemetry_power.node_id,
                            last_heard_at=node_telemetry_power.update_at,
                        )
                    )

                # 檢查 NodeTelemetryPower 是否存在
                existing_node_telemetry_power = (
                    await session.execute(
                        select(NodeTelemetryPower)
                        .where(
                            NodeTelemetryPower.node_id == node_telemetry_power.node_id
                        )
                        .where(
                            NodeTelemetryPower.create_at
                            == node_telemetry_power.create_at
                        )
                    )
                ).scalar()

                # 如果 NodeTelemetryPower 存在，但傳入比較舊，則直接回傳
                if (
                    existing_node_telemetry_power is not None
                    and node_telemetry_power.update_at
                    < existing_node_telemetry_power.update_at
                ):
                    return existing_node_telemetry_power

                # 動態構建 set_ 字典，移除值為 None 的鍵
                data = {
                    "ch1_voltage": node_telemetry_power.ch1_voltage,
                    "ch1_current": node_telemetry_power.ch1_current,
                    "ch2_voltage": node_telemetry_power.ch2_voltage,
                    "ch2_current": node_telemetry_power.ch2_current,
                    "ch3_voltage": node_telemetry_power.ch3_voltage,
                    "ch3_current": node_telemetry_power.ch3_current,
                    "update_at": node_telemetry_power.update_at,
                    "topic": node_telemetry_power.topic,
                }
                data = {k: v for k, v in data.items() if v is not None}

                # 使用 ON CONFLICT 子句來新增或更新
                stmt = (
                    insert(NodeTelemetryPower)
                    .values(
                        node_id=node_telemetry_power.node_id,
                        create_at=node_telemetry_power.create_at,
                        **data,
                    )
                    .on_conflict_do_update(
                        index_elements=["node_id", "create_at"],
                        set_=data,
                    )
                )
                await session.execute(stmt)
                await session.commit()
                final_node_telemetry_power = (
                    await session.execute(
                        select(NodeTelemetryPower)
                        .where(
                            NodeTelemetryPower.node_id == node_telemetry_power.node_id
                        )
                        .where(
                            NodeTelemetryPower.create_at
                            == node_telemetry_power.create_at
                        )
                    )
                ).scalar()
                return final_node_telemetry_power
            except Exception as e:
                await session.rollback()
                raise e
            finally:
                await session.close()

    # 取得資料
    def get_telemetry_value_or_none(self, metrics, key):
        value = metrics.get(key, None)
        if value == "NaN" or (
            isinstance(value, float)
            and math.isnan(value)
            and isinstance(value, numbers.Number)
        ):
            return None
        return value
