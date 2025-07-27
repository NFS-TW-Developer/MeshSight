"""create node_telemetry_device table

Revision ID: 26418b4dd8e9
Revises: a51ea2d3b881
Create Date: 2024-08-11 12:53:11.832733

"""

from typing import Sequence, Union
import uuid

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "26418b4dd8e9"
down_revision: Union[str, None] = "a51ea2d3b881"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "node_telemetry_device",
        sa.Column("uuid", sa.UUID(as_uuid=True), default=uuid.uuid4),
        sa.Column(
            "node_id",
            sa.BigInteger,
            sa.ForeignKey("node.id", ondelete="CASCADE"),
            nullable=False,
            primary_key=True,
        ),
        sa.Column("battery_level", sa.Integer, nullable=True),
        sa.Column("voltage", sa.Float, nullable=True),
        sa.Column("channel_utilization", sa.Float, nullable=True),
        sa.Column("air_util_tx", sa.Float, nullable=True),
        sa.Column("uptime_seconds", sa.Integer, nullable=True),
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
    op.drop_table("node_telemetry_device")
    pass
