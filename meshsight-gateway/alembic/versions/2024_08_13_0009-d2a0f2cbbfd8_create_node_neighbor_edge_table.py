"""create node_neighbor_edge table

Revision ID: d2a0f2cbbfd8
Revises: 7bc22b1d0a85
Create Date: 2024-08-11 14:55:51.542860

"""

from typing import Sequence, Union
import uuid

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "d2a0f2cbbfd8"
down_revision: Union[str, None] = "7bc22b1d0a85"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "node_neighbor_edge",
        sa.Column("uuid", sa.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column(
            "node_id",
            sa.BigInteger,
            sa.ForeignKey("node.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "edge_node_id",
            sa.BigInteger,
            sa.ForeignKey("node.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("snr", sa.Float, nullable=True),
    )
    pass


def downgrade() -> None:
    op.drop_table("node_neighbor_edge")
    pass
