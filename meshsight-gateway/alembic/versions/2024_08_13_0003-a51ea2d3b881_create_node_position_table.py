"""create node_position table

Revision ID: a51ea2d3b881
Revises: 31e575e17714
Create Date: 2024-08-11 11:21:25.811752

"""

from typing import Sequence, Union
import uuid

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "a51ea2d3b881"
down_revision: Union[str, None] = "31e575e17714"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "node_position",
        sa.Column("uuid", sa.UUID(as_uuid=True), default=uuid.uuid4),
        sa.Column(
            "node_id",
            sa.BigInteger,
            sa.ForeignKey("node.id", ondelete="CASCADE"),
            nullable=False,
            primary_key=True,
        ),
        sa.Column("latitude", sa.Float, nullable=False),
        sa.Column("longitude", sa.Float, nullable=False),
        sa.Column("altitude", sa.Float, nullable=True),
        sa.Column("precision_bits", sa.Integer, nullable=True),
        sa.Column("sats_in_view", sa.Integer, nullable=True),
        sa.Column(
            "create_at",
            sa.DateTime(timezone=True),
            nullable=False,
            primary_key=True,
        ),
        sa.Column(
            "update_at",
            sa.DateTime(timezone=True),
            nullable=False,
            default=sa.func.now(),
        ),
        sa.Column("topic", sa.String(512), nullable=False, primary_key=True),
    )
    pass


def downgrade() -> None:
    op.drop_table("node_position")
    pass
