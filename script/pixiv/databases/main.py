from sqlalchemy import create_engine, MetaData, Table, Column, Integer, Date, String, Float, Index, Text
from sqlalchemy.ext.declarative import declarative_base
from core.database import CoreDataSpace
from ..items import TaskMetaResultItem, TaskNovelItem, DatabaseIllustItem, DatabaseNovelItem
import time
import datetime

Base = declarative_base()


class Illust(Base):
    __tablename__ = 'illusts'
    __table_args__ = (
        Index('illusts_illust_id', 'illust_id'),
        Index('illust_type', 'type'),
    )
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    illust_id = Column(String, nullable=False)
    author_id = Column(String, nullable=False)
    count = Column(Integer, nullable=False)
    upload_date = Column(Integer, nullable=False)
    description = Column(String, nullable=False)
    type = Column(String, nullable=False)


class Author(Base):
    __tablename__ = 'authors'
    __table_args__ = (
        Index('author_id', 'author_id'),
    )
    id = Column(Integer, primary_key=True, autoincrement=True)
    author_id = Column(String, nullable=False)
    name = Column(String, nullable=False)


class Tag(Base):
    __tablename__ = 'tags'
    __table_args__ = (
        Index('name', 'name'),
    )
    id = Column(Integer, primary_key=True, autoincrement=True)
    illust_id = Column(String, nullable=False)
    name = Column(String, nullable=False)


class ResourceIllust(Base):
    __tablename__ = 'resources_illust'
    __table_args__ = (
        Index('resources_illust_illust_id', 'illust_id'),
    )
    id = Column(Integer, primary_key=True, autoincrement=True)
    illust_id = Column(String, nullable=False)
    source = Column(String, nullable=False)
    path = Column(String, nullable=False)


class ResourceNovels(Base):
    __tablename__ = 'resources_novel'
    __table_args__ = (
        Index('resources_novel_illust_id', 'illust_id'),
    )
    id = Column(Integer, primary_key=True, autoincrement=True)
    illust_id = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    path = Column(String, nullable=False)


class MainSpace(CoreDataSpace):
    model_base = Base

    @classmethod
    def skip_complete(cls, item: DatabaseIllustItem):
        _session = cls.session()
        _exist_query = _session.query(Illust).filter(Illust.illust_id == item['id'])
        _exist = _session.query(_exist_query.exists()).scalar()
        return _exist

    @classmethod
    def mark_complete(cls, item: DatabaseIllustItem):
        if cls.skip_complete(item) is True:
            return False
        _session = cls.session()
        _time = time.mktime(datetime.datetime.fromisoformat(item['upload_date']).timetuple())

        _illust = Illust(
            illust_id=item['id'],
            name=item['title'],
            author_id=item['author']['id'],
            count=item['count'],
            upload_date=_time,
            description=item['description'],
            type=item['type']
        )
        _session.add(_illust)

        _author = Author(
            author_id=item['author']['id'],
            name=item['author']['name']
        )
        for tag in item['tags']:
            _tag = Tag(
                illust_id=item['id'],
                name=tag
            )
            _session.add(_tag)

        for result in item['results']:
            _result = ResourceIllust(
                illust_id=item['id'],
                source=result['url'],
                path=result['path'],
            )
            _session.add(_result)

        if isinstance(item, DatabaseNovelItem):
            _result_novel = ResourceNovels(
                illust_id=item['id'],
                content=item['content'],
                path=item['path'],
            )
            _session.add(_result_novel)

        _session.add(_author)
        _session.commit()
        return True
