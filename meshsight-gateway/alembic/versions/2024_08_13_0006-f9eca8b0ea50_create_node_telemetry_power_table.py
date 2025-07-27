"""create node_telemetry_power table

Revision ID: f9eca8b0ea50
Revises: d20800fbd52b
Create Date: 2024-08-11 13:54:13.181700

"""
from typing import Sequence, Union
import uuid

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f9eca8b0ea50'
down_revision: Union[str, None] = 'd20800fbd52b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "node_telemetry_power",
        sa.Column("uuid", sa.UUID(as_uuid=True), default=uuid.uuid4),
        sa.Column(
            "node_id",
            sa.BigInteger,
            sa.ForeignKey("node.id", ondelete="CASCADE"),
            nullable=False,
            primary_key=True,
        ),
        sa.Column("ch1_voltage", sa.Float, nullable=True),
        sa.Column("ch1_current", sa.Float, nullable=True),
        sa.Column("ch2_voltage", sa.Float, nullable=True),
        sa.Column("ch2_current", sa.Float, nullable=True),
        sa.Column("ch3_voltage", sa.Float, nullable=True),
        sa.Column("ch3_current", sa.Float, nullable=True),
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
        sa.Column("topic", sa.String(512), nullable=False),
    )
    pass


def downgrade() -> None:
    op.drop_table("node_telemetry_power")
    pass
