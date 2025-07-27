import sqlalchemy as sa
import uuid
from app.models.BaseModel import EntityMeta


class NodeTelemetryDevice(EntityMeta):
    __tablename__ = "node_telemetry_device"

    uuid = sa.Column(sa.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    node_id = sa.Column(
        sa.BigInteger,
        sa.ForeignKey("node.id", ondelete="CASCADE"),
        nullable=False,
    )
    battery_level = sa.Column(sa.Integer, nullable=True)
    voltage = sa.Column(sa.Float, nullable=True)
    channel_utilization = sa.Column(sa.Float, nullable=True)
    air_util_tx = sa.Column(sa.Float, nullable=True)
    uptime_seconds = sa.Column(sa.Integer, nullable=True)
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
