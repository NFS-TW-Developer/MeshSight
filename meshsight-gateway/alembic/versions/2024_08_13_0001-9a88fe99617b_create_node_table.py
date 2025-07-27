"""create node table

Revision ID: 9a88fe99617b
Revises: 
Create Date: 2024-08-10 13:58:49.747819

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "9a88fe99617b"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "node",
        sa.Column("id", sa.BigInteger, nullable=False, primary_key=True),
        sa.Column("id_hex", sa.String(64), nullable=False),
        sa.Column("last_heard_at", sa.DateTime(timezone=True), default=sa.func.now()),
    )
    pass


def downgrade() -> None:
    op.drop_table("node")
    pass
