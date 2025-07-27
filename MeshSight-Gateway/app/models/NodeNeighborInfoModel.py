import sqlalchemy as sa
import uuid
from app.models.BaseModel import EntityMeta


class NodeNeighborInfo(EntityMeta):
    __tablename__ = "node_neighbor_info"

    uuid = sa.Column(sa.UUID(as_uuid=True), default=uuid.uuid4)
    node_id = sa.Column(
        sa.BigInteger,
        sa.ForeignKey("node.id", ondelete="CASCADE"),
        nullable=False,
        primary_key=True,
    )
    last_sent_by_id = sa.Column(
        sa.BigInteger,
        sa.ForeignKey("node.id", ondelete="CASCADE"),
        nullable=False,
    )
    node_broadcast_interval_secs = sa.Column(sa.Integer, nullable=True)
    update_at = sa.Column(
        sa.DateTime(timezone=True), nullable=False, default=sa.func.now()
    )
    topic = sa.Column(sa.String(512), nullable=False)
