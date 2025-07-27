"""set node_info long_name and short_name deafult

Revision ID: 32026eba5a1d
Revises: 30f72dd509bf
Create Date: 2024-08-16 16:06:10.037187+00:00

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "32026eba5a1d"
down_revision: Union[str, None] = "30f72dd509bf"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 將 node_info.long_name 和 node_info.short_name 設定預設值為 'UNK'
    op.alter_column("node_info", "long_name", server_default="UNK")
    op.alter_column("node_info", "short_name", server_default="UNK")
    pass


def downgrade() -> None:
    op.alter_column("node_info", "short_name", server_default=None)
    op.alter_column("node_info", "long_name", server_default=None)
    pass
