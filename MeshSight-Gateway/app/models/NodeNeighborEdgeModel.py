import sqlalchemy as sa
import uuid
from app.models.BaseModel import EntityMeta


class NodeNeighborEdge(EntityMeta):
    __tablename__ = "node_neighbor_edge"

    uuid = sa.Column(sa.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    node_id = sa.Column(
        sa.BigInteger,
        sa.ForeignKey("node.id", ondelete="CASCADE"),
        nullable=False,
    )
    edge_node_id = sa.Column(
        sa.BigInteger,
        sa.ForeignKey("node.id", ondelete="CASCADE"),
        nullable=False,
    )
    snr = sa.Column(sa.Float, nullable=True)
