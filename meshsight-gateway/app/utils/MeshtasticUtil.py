import logging
import math
import random

logger = logging.getLogger(__name__)


class MeshtasticUtil:

    # 將定位資訊模糊處理到指定的距離
    def blur_position(lat: float, lon: float, distance: int):
        # 將緯度和經度轉換為弧度
        lat_rad = math.radians(lat)
        lon_rad = math.radians(lon)

        # 計算經度和緯度的偏移量（地球半徑約為 6371 公里）
        delta_lat = distance / 6371000  # 將距離轉換為弧度
        delta_lon = distance / (6371000 * math.cos(lat_rad))  # 將距離轉換為弧度

        # 產生隨機的偏移量
        random_lat = lat_rad + random.uniform(-delta_lat, delta_lat)
        random_lon = lon_rad + random.uniform(-delta_lon, delta_lon)

        # 將弧度轉換回度
        return (math.degrees(random_lat), math.degrees(random_lon))

    def convert_node_id_from_int_to_hex(id: int):
        id_hex = f"{id:08x}"
        return id_hex

    def convert_node_id_from_hex_to_int(id: str):
        if id.startswith("!"):
            id = id.replace("!", "")
        return int(id, 16)

    # 精度轉公尺
    def convert_precision_to_meter(precision: int):
        # 來自 Meshtastic Web 的定義:　https://github.com/meshtastic/web/blob/2b34d78a86f8dd432572b4ac0a3c2448db9082c9/src/components/PageComponents/Channel.tsx#L175
        precision_mapping = {
            10: 23000,
            11: 12000,
            12: 5800,
            13: 2900,
            14: 1500,
            15: 700,
            16: 350,
            17: 200,
            18: 90,
            19: 50,
            32: 0,  # 0 表示精確位置
        }
        if precision is None:
            return None
        elif 1 <= precision <= 9:
            precision = 10
        elif 20 <= precision <= 31:
            precision = 19
        return precision_mapping.get(precision, -1)  # -1 表示未知的精確度值

    # 計算兩點之間的距離
    def calculate_distance_in_meters(
        lat1: float, lon1: float, lat2: float, lon2: float
    ):
        # 將緯度和經度從度數轉換為弧度
        lat1_rad = math.radians(lat1)
        lon1_rad = math.radians(lon1)
        lat2_rad = math.radians(lat2)
        lon2_rad = math.radians(lon2)

        # 計算緯度和經度之間的差異
        delta_lat = lat2_rad - lat1_rad
        delta_lon = lon2_rad - lon1_rad

        # 使用 Haversine 公式計算距離
        a = (
            math.sin(delta_lat / 2) ** 2
            + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lon / 2) ** 2
        )
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        distance_km = 6371 * c  # 地球半徑（公里）

        distance_m = distance_km * 1000  # 將距離轉換為公尺
        return distance_m

    def get_root_topic_from_topic(topic):
        # 尋找 /2/ 的位置
        index = topic.find("/2/")
        if index != -1:
            # 取前面的字串
            root_topic = topic[:index]
        else:
            # 如果找不到 /2/，則返回原始 topic
            root_topic = topic
        return root_topic

    def get_channel_from_topic(topic):
        return (
            f"{topic.split('/')[-2]}(MapReport)"
            if topic.split("/")[-2] == "map"
            else (
                f"{topic.split('/')[-2]}(json)"
                if topic.split("/")[-3] == "json"
                else topic.split("/")[-2]
            )
        )
