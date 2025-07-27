"""create analysis_device_active_hourly table

Revision ID: 5ef81b888b74
Revises: d2a0f2cbbfd8
Create Date: 2024-08-13 12:23:15.920039+00:00

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "5ef81b888b74"
down_revision: Union[str, None] = "d2a0f2cbbfd8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "analysis_device_active_hourly",
        sa.Column("hourly", sa.DateTime(timezone=True), primary_key=True),
        sa.Column("known_count", sa.Integer, nullable=False),
        sa.Column("unknown_count", sa.Integer, nullable=False),
    )
    pass


def downgrade() -> None:
    op.drop_table("analysis_device_active_hourly")
    pass
