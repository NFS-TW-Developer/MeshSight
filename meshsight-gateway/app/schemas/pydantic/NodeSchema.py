from datetime import datetime
from typing import Dict, List, Optional
from pydantic import BaseModel


class ResolvedAddressItem(BaseModel):
    fullAddress: Optional[str]  # 完整地址
    houseNumber: Optional[str]
    road: Optional[str]
    neighbourhood: Optional[str]
    district: Optional[str]
    city: Optional[str]
    county: Optional[str]
    state: Optional[str]
    postcode: Optional[str]
    country: Optional[str]
    countryCode: Optional[str]
    raw: Optional[Dict]  # 原始 address dict，備用


class InfoItem(BaseModel):
    longName: str  # 長名稱
    shortName: str  # 短名稱
    hardware: Optional[str]  # 硬體
    isLicensed: bool  # 執照狀態
    role: str  # 角色
    firmware: Optional[str]  # 韌體
    loraRegion: Optional[str]  # LoRa 區域
    loraModemPreset: Optional[str]  # LoRa Modem preset
    hasDefaultChannel: bool  # 是否有預設頻道
    numOnlineLocalNodes: int  # 本地節點數
    updateAt: datetime  # 更新時間
    channel: str  # 頻道
    rootTopic: str  # 根主題


class PositionItem(BaseModel):
    latitude: float  # 緯度
    longitude: float  # 經度
    altitude: Optional[float]  # 高度
    precisionBit: Optional[int]  # 精度
    precisionInMeters: Optional[int]  # 精度轉公尺
    satsInView: Optional[int]  # 可見衛星數
    updateAt: datetime  # 更新時間
    viaId: int  # 來源 node ID
    viaIdHex: str  # 來源 node ID HEX
    channel: str  # 頻道
    rootTopic: str  # 根主題
    resolvedAddress: Optional[ResolvedAddressItem]  # 解析後的地址資訊


class TelemetryDeviceItem(BaseModel):
    batteryLevel: Optional[float]  # 電池電量
    voltage: Optional[float]  # 電壓
    channelUtilization: Optional[float]  # 頻道利用率
    airUtilTx: Optional[float]  # 空中利用率 TX
    createAt: datetime  # 時間
    updateAt: datetime  # 更新時間
    viaId: int  # 來源 node ID
    viaIdHex: str  # 來源 node ID HEX
    channel: str  # 頻道
    rootTopic: str  # 根主題


class NodeInfoResponse(BaseModel):
    id: int  # ID
    idHex: str  # ID HEX
    item: InfoItem  # 資訊


class NodePositionResponse(BaseModel):
    id: int  # ID
    idHex: str  # ID HEX
    position: Optional[PositionItem]  # 位置資訊


class NodeTelemetryDeviceResponse(BaseModel):
    id: int  # ID
    idHex: str  # ID HEX
    items: List[TelemetryDeviceItem]  # 遙測資訊
