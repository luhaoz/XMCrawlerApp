# -*- mode: python -*-
import scrapy


class CoreItem(scrapy.Item):
    def __setitem__(self, key, value):
        if key in self.fields:
            self._values[key] = value


class AuthorItem(CoreItem):
    id = scrapy.Field()
    name = scrapy.Field()


class TaskMetaItem(CoreItem):
    id = scrapy.Field()
    title = scrapy.Field()
    tags = scrapy.Field()
    description = scrapy.Field()
    author = scrapy.Field()
    upload_date = scrapy.Field()
    count = scrapy.Field()
    type = scrapy.Field()


class TaskMetaResultItem(TaskMetaItem):
    results = scrapy.Field()


class DatabaseIllustItem(TaskMetaItem):
    results = scrapy.Field()


class DatabaseNovelItem(DatabaseIllustItem):
    content = scrapy.Field()
    path = scrapy.Field()


class TaskItem(TaskMetaItem):
    source = scrapy.Field()
    space = scrapy.Field()


class TaskNovelItem(TaskItem):
    content = scrapy.Field()
    path = scrapy.Field()


class SourceItem(CoreItem):
    type = scrapy.Field()
    url = scrapy.Field()
    sources = scrapy.Field()
