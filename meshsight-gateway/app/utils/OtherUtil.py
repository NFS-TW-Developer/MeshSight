import logging
import math
import os
import traceback
from datetime import datetime
from app.utils.ConfigUtil import ConfigUtil

logger = logging.getLogger(__name__)


class OtherUtil:

    # 檢查並處理 NaN 值
    def sanitize_value(value):
        if isinstance(value, float) and math.isnan(value):
            return None
        return value

    def read_cache_json(filename: str) -> str:
        try:
            cache_file_path = (
                f"{ConfigUtil().read_config()['cache']['path']}/{filename}.json"
            )
            os.makedirs(os.path.dirname(cache_file_path), exist_ok=True)
            if not os.path.exists(cache_file_path):
                # 如果不存在，則回傳 None
                return None
            if (
                os.path.getmtime(cache_file_path)
                < datetime.now().timestamp() - ConfigUtil().read_config()["cache"]["ttl"]
            ):
                # 如果已經過期，則回傳 None
                return None
            with open(cache_file_path, "r") as cache_file:
                content = cache_file.read()
                if not content:
                    # 如果檔案內容為空，則回傳 None
                    return None
                return content
        except Exception as e:
            stacktrace = traceback.format_exc()
            logger.info(stacktrace)
            raise e

    def write_cache_json(filename: str, data: str):
        try:
            cache_file_path = (
                f"{ConfigUtil().read_config()['cache']['path']}/{filename}.json"
            )
            os.makedirs(os.path.dirname(cache_file_path), exist_ok=True)
            with open(cache_file_path, "w") as cache_file:
                cache_file.write(data)
        except Exception as e:
            stacktrace = traceback.format_exc()
            logger.info(stacktrace)
            raise e
