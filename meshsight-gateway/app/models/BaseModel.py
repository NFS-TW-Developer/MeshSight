from sqlalchemy.ext.declarative import declarative_base

from app.configs.Database import Engine

# Base Entity Model Schema
EntityMeta = declarative_base()


# def initialize_database():
#     # 建立所有資料表，如果資料表不存在
#     EntityMeta.metadata.create_all(bind=Engine, checkfirst=True)
