import asyncio
import logging
import os
from alembic.config import Config
from alembic import command
from app.configs.Scheduler import start_scheduler, shutdown_scheduler
from app.routers import routers
from app.services.SystemSchedulerService import SystemSchedulerService
from app.services.MqttListenerService import MqttListenerService
from app.utils.ConfigUtil import ConfigUtil
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# 設定檔讀取
config = ConfigUtil().read_config()

logger = logging.getLogger(__name__)
logger.setLevel(config.get("log", {}).get("level", "INFO").upper())

@asynccontextmanager
async def lifespan(app: FastAPI):
    start_scheduler()
    yield
    shutdown_scheduler()


# FastAPI app 設定
app = FastAPI(lifespan=lifespan)

# CORS middleware 設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 路由設定
for router in routers:
    app.include_router(router)

async def start_api():
    logger.info("API 服務正在啟動...")
    process = await asyncio.create_subprocess_exec(
        "gunicorn",
        "-c",
        os.path.join(
            os.getcwd(), "app/gunicorn.conf.py"
        ),  # 讓 Gunicorn 使用 gunicorn.conf.py
        "app.main:app",
    )
    await process.communicate()
    logger.info("API 服務已啟動")


async def start_mqtt_listener():
    logger.info("MQTT Linstener 正在啟動...")
    task_job = asyncio.create_task(MqttListenerService().start())
    logger.info("MQTT Linstener 已啟動")


def start_scheduler_job():
    logger.info("正在啟動排程任務......")
    scheduler_async = AsyncIOScheduler()
    scheduler_async.add_job(
        SystemSchedulerService().analyze_active_device, CronTrigger(minute=0)
    )  # 每小時整點執行，分析活躍裝置
    scheduler_async.add_job(
        SystemSchedulerService().clear_cache, CronTrigger(hour=0, minute=30)
    )  # 每天 00:30 執行，清除 cache
    scheduler_async.add_job(
        SystemSchedulerService().clear_node_position, CronTrigger(minute=28)
    )  # 每小時 28 分執行，清除過期的 node_position 資料
    scheduler_async.add_job(
        SystemSchedulerService().clear_node_neighbor_info, CronTrigger(minute=32)
    )  # 每小時 32 分執行，清除過期的 node_neighbor_info 資料
    scheduler_async.start()

async def main():
    logger.info("meshsight-gateway is running...")
    # 等待 5 秒以確保服務啟動
    await asyncio.sleep(5)
    logger.info("正在初始化資料模型屬性...")
    alembic_cfg = Config("alembic.ini")
    command.upgrade(alembic_cfg, "head")
    # 啟動排程任務
    start_scheduler_job()
    logger.info("正在啟動子服務......")
    api_task = asyncio.create_task(start_api())
    mqtt_listener_task = asyncio.create_task(start_mqtt_listener())
    # 並行運行子服務
    await asyncio.gather(asyncio.Future(), api_task, mqtt_listener_task)
