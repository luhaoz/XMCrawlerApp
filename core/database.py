from sqlalchemy import create_engine, MetaData, Table, Column, Integer, Date, String, Float, Index, Text
from sqlalchemy.orm import sessionmaker
import os


class CoreDataSpace(object):
    _engine = None
    model_base = None

    @classmethod
    def space(cls, path):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        cls._engine = create_engine("sqlite:///%s" % path)
        cls.init()
        return cls

    @classmethod
    def session(cls):
        Session = sessionmaker(bind=cls._engine)
        return Session()

    @classmethod
    def engine(cls):
        return cls._engine

    @classmethod
    def init(cls):
        cls.model_base.metadata.create_all(cls._engine)
        return cls


class DataSpaces(object):
    _pool = dict()

    @classmethod
    def set(cls, path, space: CoreDataSpace):
        cls._pool[path] = space

    @classmethod
    def get(cls, path):
        return cls._pool[path]
