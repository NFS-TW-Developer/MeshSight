import sqlalchemy as sa
from app.models.BaseModel import EntityMeta


class AnalysisDeviceActiveHourly(EntityMeta):
    __tablename__ = "analysis_device_active_hourly"

    hourly = sa.Column(sa.DateTime(timezone=True), nullable=False, primary_key=True)
    known_count = sa.Column(sa.Integer, nullable=False)
    unknown_count = sa.Column(sa.Integer, nullable=False)
