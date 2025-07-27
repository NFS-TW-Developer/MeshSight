import logging
import os
import traceback
import uuid
import yaml
from datetime import datetime
from filelock import FileLock

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ConfigUtil:

    def __init__(self, check_and_merge: bool = False) -> None:
        self.logger = logging.getLogger(__name__)
        self.config_dir = os.path.join(os.getcwd(), "configs")
        self.default_config_path = os.path.join(
            os.getcwd(), "app/configs/default/config.yml"
        )
        self.config_path = os.path.join(self.config_dir, "config.yml")
        self.lock = FileLock(self.config_path + ".lock")
        self.ensure_config_exists(check_and_merge)

    def ensure_config_exists(self, check_and_merge: bool = False):
        """確保配置檔案存在，如果不存在則從預設配置複製一份，並同步比較差異"""
        if not os.path.exists(self.config_path):
            os.makedirs(self.config_dir, exist_ok=True)
            with open(self.default_config_path, "r", encoding="utf-8") as default_file:
                with open(self.config_path, "w", encoding="utf-8") as config_file:
                    config_file.write(default_file.read())
        else:
            if check_and_merge:
                # 如果 config.yml 存在，檢查並補充/刪除配置項
                try:
                    # 使用鎖確保單一進程訪問
                    with self.lock:
                        # 先備份原始配置檔案
                        backup_path = (
                            self.config_path
                            + f".bak.{datetime.now().strftime('%Y%m%d%H%M%S')}"
                        )
                        with open(
                            self.config_path, "r", encoding="utf-8"
                        ) as original_file:
                            with open(
                                backup_path, "w", encoding="utf-8"
                            ) as backup_file:
                                backup_file.write(original_file.read())

                        with open(
                            self.default_config_path, "r", encoding="utf-8"
                        ) as default_file:
                            default_config = yaml.safe_load(default_file)

                        current_config = self.read_config()

                        # 檢查並補充缺失的配置項
                        self.merge_configs(current_config, default_config)

                        # 檢查並刪除多餘的配置項
                        self.remove_extra_configs(current_config, default_config)

                        # 最後將更新後的配置寫回檔案
                        with open(
                            self.config_path, "w", encoding="utf-8"
                        ) as config_file:
                            yaml.dump(current_config, config_file)
                    # 完成後刪除備份檔案
                    if os.path.exists(backup_path):
                        os.remove(backup_path)
                    self.logger.info("配置已檢查並更新。")
                except Exception as e:
                    self.logger.error(
                        "檢查和更新配置時發生錯誤: %s",
                        traceback.format_exc(),
                    )
                    # 如果發生異常，嘗試從備份恢復
                    if os.path.exists(backup_path):
                        try:
                            with open(
                                backup_path, "r", encoding="utf-8"
                            ) as backup_file:
                                with open(
                                    self.config_path, "w", encoding="utf-8"
                                ) as config_file:
                                    config_file.write(backup_file.read())
                            self.logger.warning("配置已從備份恢復。")
                        except Exception as restore_e:
                            self.logger.error(f"從備份恢復失敗: {str(restore_e)}")
                    raise e

    def merge_configs(self, current_config, default_config):
        """補充缺失的配置項"""
        if current_config is None:
            current_config = {}

        for key, value in default_config.items():
            if key not in current_config:
                current_config[key] = value
            elif isinstance(value, dict) and isinstance(current_config.get(key), dict):
                self.merge_configs(current_config[key], value)  # 遞迴合併

    def remove_extra_configs(self, current_config, default_config):
        """刪除多餘的配置項"""
        keys_to_delete = []
        for key in current_config:
            if key not in default_config:
                keys_to_delete.append(key)
            elif isinstance(current_config[key], dict) and isinstance(
                default_config.get(key), dict
            ):
                self.remove_extra_configs(
                    current_config[key], default_config[key]
                )  # 遞迴處理

        for key in keys_to_delete:
            del current_config[key]

    def read_config(self):
        """讀取配置檔案"""
        try:
            with open(self.config_path, "r", encoding="utf-8") as file:
                return yaml.safe_load(file)
        except Exception as e:
            self.logger.error("讀取配置檔案時發生錯誤: %s", traceback.format_exc())
            raise e

    # 取得某個 key 的值
    def get_config(self, key, default=None):
        """取得某個 key 的值"""
        try:
            config = self.read_config()
            keys = key.split(".")
            value = config
            for k in keys:
                if k not in value:
                    return default
                value = value[k]
            return value
        except Exception as e:
            self.logger.error("取得配置值時發生錯誤: %s", traceback.format_exc())
            raise e

    def edit_config(self, key, value):
        """編輯某個 key 的值"""
        try:
            config = self.read_config()
            keys = key.split(".")
            d = config
            for k in keys[:-1]:
                if k not in d:
                    d[k] = {}
                d = d[k]
            d[keys[-1]] = value
            with open(self.config_path, "w", encoding="utf-8") as file:
                yaml.dump(config, file)
        except Exception as e:
            self.logger.error("編輯配置值時發生錯誤: %s", traceback.format_exc())
            raise e

    # 取得 stationUuid 的值
    def get_station_uuid(self):
        config = self.read_config()
        if "magicai-platform-server" not in config:
            config["magicai-platform-server"] = {}
        if (
            "uuid" not in config["magicai-platform-server"]
            or not config["magicai-platform-server"]["uuid"]
        ):
            station_uuid = str(uuid.uuid4())
            self.edit_config("magicai-platform-server.uuid", station_uuid)
        else:
            station_uuid = config["magicai-platform-server"]["uuid"]
        return station_uuid
