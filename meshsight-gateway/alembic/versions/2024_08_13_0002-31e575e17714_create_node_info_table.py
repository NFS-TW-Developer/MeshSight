"""create node_info table

Revision ID: 31e575e17714
Revises: 9a88fe99617b
Create Date: 2024-08-10 14:03:13.589682

"""

from typing import Sequence, Union
import uuid

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "31e575e17714"
down_revision: Union[str, None] = "9a88fe99617b"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "node_info",
        sa.Column("uuid", sa.UUID(as_uuid=True), default=uuid.uuid4),
        sa.Column(
            "node_id",
            sa.BigInteger,
            sa.ForeignKey("node.id", ondelete="CASCADE"),
            nullable=False,
            primary_key=True,
        ),
        sa.Column("long_name", sa.String(64), nullable=False),
        sa.Column("short_name", sa.String(16), nullable=False),
        sa.Column("hw_model", sa.String(64), nullable=True),
        sa.Column("is_licensed", sa.Boolean, nullable=False, default=False),
        sa.Column("role", sa.String(16), nullable=True),
        sa.Column("firmware_version", sa.String(64), nullable=True),
        sa.Column("lora_region", sa.String(16), nullable=True),
        sa.Column("lora_modem_preset", sa.String(24), nullable=True),
        sa.Column("has_default_channel", sa.Boolean, nullable=False, default=False),
        sa.Column("num_online_local_nodes", sa.Integer, nullable=False, default=0),
        sa.Column(
            "update_at",
            sa.DateTime(timezone=True),
            nullable=False,
            default=sa.func.now(),
        ),
        sa.Column("topic", sa.String(512), nullable=False),
    )
    pass


def downgrade() -> None:
    op.drop_table("node_info")
    pass
