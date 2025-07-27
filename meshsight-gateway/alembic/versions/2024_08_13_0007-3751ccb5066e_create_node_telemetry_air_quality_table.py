"""create node_telemetry_air_quality table

Revision ID: 3751ccb5066e
Revises: f9eca8b0ea50
Create Date: 2024-08-11 13:58:50.981535

"""

from typing import Sequence, Union
import uuid

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "3751ccb5066e"
down_revision: Union[str, None] = "f9eca8b0ea50"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "node_telemetry_air_quality",
        sa.Column("uuid", sa.UUID(as_uuid=True), default=uuid.uuid4),
        sa.Column(
            "node_id",
            sa.BigInteger,
            sa.ForeignKey("node.id", ondelete="CASCADE"),
            nullable=False,
            primary_key=True,
        ),
        sa.Column("pm10_standard", sa.Integer, nullable=True),
        sa.Column("pm25_standard", sa.Integer, nullable=True),
        sa.Column("pm100_standard", sa.Integer, nullable=True),
        sa.Column("pm10_environmental", sa.Integer, nullable=True),
        sa.Column("pm25_environmental", sa.Integer, nullable=True),
        sa.Column("pm100_environmental", sa.Integer, nullable=True),
        sa.Column("particles_03um", sa.Integer, nullable=True),
        sa.Column("particles_05um", sa.Integer, nullable=True),
        sa.Column("particles_10um", sa.Integer, nullable=True),
        sa.Column("particles_25um", sa.Integer, nullable=True),
        sa.Column("particles_50um", sa.Integer, nullable=True),
        sa.Column("particles_100um", sa.Integer, nullable=True),
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
    op.drop_table("node_telemetry_air_quality")
    pass
