import sqlalchemy as sa
import uuid
from app.models.BaseModel import EntityMeta


class NodePosition(EntityMeta):
    __tablename__ = "node_position"

    uuid = sa.Column(sa.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    node_id = sa.Column(
        sa.BigInteger,
        sa.ForeignKey("node.id", ondelete="CASCADE"),
        nullable=False,
    )
    latitude = sa.Column(sa.Float, nullable=False)
    longitude = sa.Column(sa.Float, nullable=False)
    altitude = sa.Column(sa.Float, nullable=True)
    precision_bits = sa.Column(sa.Integer, nullable=True)
    sats_in_view = sa.Column(sa.Integer, nullable=True)
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
    topic = sa.Column(sa.String(512), nullable=False, primary_key=True)
