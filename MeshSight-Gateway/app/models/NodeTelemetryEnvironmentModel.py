import sqlalchemy as sa
import uuid
from app.models.BaseModel import EntityMeta


class NodeTelemetryEnvironment(EntityMeta):
    __tablename__ = "node_telemetry_environment"

    uuid = sa.Column(sa.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    node_id = sa.Column(
        sa.BigInteger,
        sa.ForeignKey("node.id", ondelete="CASCADE"),
        nullable=False,
    )
    temperature = sa.Column(sa.Float, nullable=True)
    relative_humidity = sa.Column(sa.Float, nullable=True)
    barometric_pressure = sa.Column(sa.Float, nullable=True)
    gas_resistance = sa.Column(sa.Float, nullable=True)
    voltage = sa.Column(sa.Float, nullable=True)
    current = sa.Column(sa.Float, nullable=True)
    iaq = sa.Column(sa.Integer, nullable=True)
    distance = sa.Column(sa.Float, nullable=True)
    lux = sa.Column(sa.Float, nullable=True)
    white_lux = sa.Column(sa.Float, nullable=True)
    ir_lux = sa.Column(sa.Float, nullable=True)
    uv_lux = sa.Column(sa.Float, nullable=True)
    wind_direction = sa.Column(sa.Integer, nullable=True)
    wind_speed = sa.Column(sa.Float, nullable=True)
    weight = sa.Column(sa.Float, nullable=True)
    wind_gust = sa.Column(sa.Float, nullable=True)
    wind_lull = sa.Column(sa.Float, nullable=True)
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
