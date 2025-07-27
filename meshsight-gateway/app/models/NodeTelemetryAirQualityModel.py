import sqlalchemy as sa
import uuid
from app.models.BaseModel import EntityMeta


class NodeTelemetryAirQuality(EntityMeta):
    __tablename__ = "node_telemetry_air_quality"

    uuid = sa.Column(sa.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    node_id = sa.Column(
        sa.BigInteger,
        sa.ForeignKey("node.id", ondelete="CASCADE"),
        nullable=False,
    )
    pm10_standard = sa.Column(sa.Integer, nullable=True)
    pm25_standard = sa.Column(sa.Integer, nullable=True)
    pm100_standard = sa.Column(sa.Integer, nullable=True)
    pm10_environmental = sa.Column(sa.Integer, nullable=True)
    pm25_environmental = sa.Column(sa.Integer, nullable=True)
    pm100_environmental = sa.Column(sa.Integer, nullable=True)
    particles_03um = sa.Column(sa.Integer, nullable=True)
    particles_05um = sa.Column(sa.Integer, nullable=True)
    particles_10um = sa.Column(sa.Integer, nullable=True)
    particles_25um = sa.Column(sa.Integer, nullable=True)
    particles_50um = sa.Column(sa.Integer, nullable=True)
    particles_100um = sa.Column(sa.Integer, nullable=True)
    create_at = sa.Column(
        sa.DateTime(timezone=True),
        nullable=False,
        primary_key=True,
    )
    update_at = sa.Column(
        sa.DateTime(timezone=True),
        nullable=False,
        default=sa.func.now(),
    )
    topic = sa.Column(sa.String(512), nullable=False)
