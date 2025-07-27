import sqlalchemy as sa
import uuid
from app.models.BaseModel import EntityMeta


class NodeTelemetryPower(EntityMeta):
    __tablename__ = "node_telemetry_power"

    uuid = sa.Column(sa.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    node_id = sa.Column(
        sa.BigInteger,
        sa.ForeignKey("node.id", ondelete="CASCADE"),
        nullable=False,
    )
    ch1_voltage = sa.Column(sa.Float, nullable=True)
    ch1_current = sa.Column(sa.Float, nullable=True)
    ch2_voltage = sa.Column(sa.Float, nullable=True)
    ch2_current = sa.Column(sa.Float, nullable=True)
    ch3_voltage = sa.Column(sa.Float, nullable=True)
    ch3_current = sa.Column(sa.Float, nullable=True)
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
