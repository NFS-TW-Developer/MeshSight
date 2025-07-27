import logging
from app.configs.Database import (
    get_db_connection,
    get_db_connection_async,
)
from datetime import datetime
from typing import List, Optional
from fastapi import Depends
from sqlalchemy import desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session
from app.models.AnalysisDeviceActiveHourlyModel import AnalysisDeviceActiveHourly


class AnalysisDeviceActiveHourlyRepository:
    db: Session
    db_async: AsyncSession

    def __init__(
        self,
        db: Session = Depends(get_db_connection),
        db_async: AsyncSession = Depends(get_db_connection_async),
    ) -> None:
        self.db = db
        self.db_async = db_async
        self.logger = logging.getLogger(__name__)

    def fetch_active_hourly_records(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ) -> List[AnalysisDeviceActiveHourly]:
        query = self.db.query(AnalysisDeviceActiveHourly)
        if start_time:
            query = query.filter(AnalysisDeviceActiveHourly.hourly >= start_time)
        if end_time:
            query = query.filter(AnalysisDeviceActiveHourly.hourly <= end_time)
        query = query.order_by(desc(AnalysisDeviceActiveHourly.hourly))
        return query.all()
