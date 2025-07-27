import sqlalchemy as sa
from app.models.BaseModel import EntityMeta


class Node(EntityMeta):
    __tablename__ = "node"

    id = sa.Column(sa.BigInteger, nullable=False, primary_key=True)
    id_hex = sa.Column(sa.String(64), nullable=False)
    last_heard_at = sa.Column(sa.DateTime(timezone=True), default=sa.func.now())
