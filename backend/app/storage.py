import os
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

Path(__file__).resolve().parents[1].joinpath('data').mkdir(exist_ok=True)
DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///' + str(Path(__file__).resolve().parents[1] / 'data' / 'marketing.db'))
engine = create_engine(DATABASE_URL, connect_args={'check_same_thread': False} if DATABASE_URL.startswith('sqlite') else {})
Session = sessionmaker(bind=engine)


class Base(DeclarativeBase):
    pass


def session():
    with Session() as db:
        yield db
