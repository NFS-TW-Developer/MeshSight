"""create node_telemetry_environment table

Revision ID: d20800fbd52b
Revises: 26418b4dd8e9
Create Date: 2024-08-11 13:33:00.396224

"""

from typing import Sequence, Union
import uuid

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "d20800fbd52b"
down_revision: Union[str, None] = "26418b4dd8e9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "node_telemetry_environment",
        sa.Column("uuid", sa.UUID(as_uuid=True), default=uuid.uuid4),
        sa.Column(
            "node_id",
            sa.BigInteger,
            sa.ForeignKey("node.id", ondelete="CASCADE"),
            nullable=False,
            primary_key=True,
        ),
        sa.Column("temperature", sa.Float, nullable=True),
        sa.Column("relative_humidity", sa.Float, nullable=True),
        sa.Column("barometric_pressure", sa.Float, nullable=True),
        sa.Column("gas_resistance", sa.Float, nullable=True),
        sa.Column("voltage", sa.Float, nullable=True),
        sa.Column("current", sa.Float, nullable=True),
        sa.Column("iaq", sa.Integer, nullable=True),
        sa.Column("distance", sa.Float, nullable=True),
        sa.Column("lux", sa.Float, nullable=True),
        sa.Column("white_lux", sa.Float, nullable=True),
        sa.Column("ir_lux", sa.Float, nullable=True),
        sa.Column("uv_lux", sa.Float, nullable=True),
        sa.Column("wind_direction", sa.Integer, nullable=True),
        sa.Column("wind_speed", sa.Float, nullable=True),
        sa.Column("weight", sa.Float, nullable=True),
        sa.Column("wind_gust", sa.Float, nullable=True),
        sa.Column("wind_lull", sa.Float, nullable=True),
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
    op.drop_table("node_telemetry_environment")
    pass
