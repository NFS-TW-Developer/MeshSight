"""create node_neighbor_info table

Revision ID: 7bc22b1d0a85
Revises: 3751ccb5066e
Create Date: 2024-08-11 14:53:20.427420

"""

from typing import Sequence, Union
import uuid

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "7bc22b1d0a85"
down_revision: Union[str, None] = "3751ccb5066e"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "node_neighbor_info",
        sa.Column("uuid", sa.UUID(as_uuid=True), default=uuid.uuid4),
        sa.Column(
            "node_id",
            sa.BigInteger,
            sa.ForeignKey("node.id", ondelete="CASCADE"),
            nullable=False,
            primary_key=True,
        ),
        sa.Column(
            "last_sent_by_id",
            sa.BigInteger,
            sa.ForeignKey("node.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("node_broadcast_interval_secs", sa.Integer, nullable=True),
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
    op.drop_table("node_neighbor_info")
    pass
