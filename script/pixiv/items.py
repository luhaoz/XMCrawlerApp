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


class TaskItem(TaskMetaItem):
    source = scrapy.Field()


class TaskNovelItem(TaskItem):
    content = scrapy.Field()


class SourceItem(CoreItem):
    type = scrapy.Field()
    url = scrapy.Field()
    sources = scrapy.Field()
