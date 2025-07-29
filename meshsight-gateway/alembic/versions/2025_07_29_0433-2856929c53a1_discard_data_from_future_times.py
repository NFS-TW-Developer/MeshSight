"""discard_data_from_future_times

Revision ID: 2856929c53a1
Revises: 32026eba5a1d
Create Date: 2025-07-29 04:33:22.277891+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2856929c53a1'
down_revision: Union[str, None] = '32026eba5a1d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 刪除 node_info 表中 update_at 在未來時間的資料
    op.execute("""
        DELETE FROM node_info
        WHERE update_at > NOW();
    """)
    # 刪除 node_neighbor_info 表中 update_at 在未來時間的資料
    op.execute("""
        DELETE FROM node_neighbor_info
        WHERE update_at > NOW();
    """)
    # 刪除 node_position 表中 update_at 在未來時間的資料
    op.execute("""
        DELETE FROM node_position
        WHERE update_at > NOW();
    """)
    pass


def downgrade() -> None:
    # 不可逆
    pass
