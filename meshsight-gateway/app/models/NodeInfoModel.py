import sqlalchemy as sa
import uuid
from app.models.BaseModel import EntityMeta


class NodeInfo(EntityMeta):
    __tablename__ = "node_info"

    uuid = sa.Column(sa.UUID(as_uuid=True), default=uuid.uuid4)
    node_id = sa.Column(
        sa.BigInteger,
        sa.ForeignKey("node.id", ondelete="CASCADE"),
        nullable=False,
        primary_key=True,
    )
    long_name = sa.Column(sa.String(64), nullable=False, default="UNK")
    short_name = sa.Column(sa.String(16), nullable=False, default="UNK")
    hw_model = sa.Column(sa.String(64), nullable=True)
    is_licensed = sa.Column(sa.Boolean, nullable=False, default=False)
    role = sa.Column(sa.String(16), nullable=False, default="CLIENT")
    firmware_version = sa.Column(sa.String(64), nullable=True)
    lora_region = sa.Column(sa.String(16), nullable=True)
    lora_modem_preset = sa.Column(sa.String(24), nullable=True)
    has_default_channel = sa.Column(sa.Boolean, nullable=False, default=False)
    num_online_local_nodes = sa.Column(sa.Integer, nullable=False, default=0)
    update_at = sa.Column(
        sa.DateTime(timezone=True),
        nullable=False,
        default=sa.func.now(),
    )
    topic = sa.Column(sa.String(512), nullable=False)
