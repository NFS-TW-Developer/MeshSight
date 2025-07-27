"""set node_info.role to nonull and default CLIENT

Revision ID: 30f72dd509bf
Revises: 5ef81b888b74
Create Date: 2024-08-14 15:21:37.892670+00:00

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "30f72dd509bf"
down_revision: Union[str, None] = "5ef81b888b74"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 先將現有 node_info.role 為 NULL 的值轉為 'CLIENT'
    op.execute(
        "UPDATE node_info SET role = 'CLIENT' WHERE role IS NULL"
    )
    # 將 node_info.role 設為 nonull 並設定預設值為 CLIENT
    op.alter_column(
        "node_info",
        "role",
        existing_type=sa.String(16),
        nullable=False,
        server_default="CLIENT",
    )
    pass


def downgrade() -> None:
    # 將 node_info.role 回復為 nullable
    op.alter_column(
        "node_info",
        "role",
        existing_type=sa.String(16),
        nullable=True,
        server_default=None,
    )
    pass
