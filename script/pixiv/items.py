# -*- mode: python -*-
import scrapy


class AuthorItem(scrapy.Item):
    id = scrapy.Field()
    name = scrapy.Field()


class TaskItem(scrapy.Item):
    id = scrapy.Field()
    title = scrapy.Field()
    tags = scrapy.Field()
    description = scrapy.Field()
    author = scrapy.Field()
    source = scrapy.Field()


class SourceItem(scrapy.Item):
    type = scrapy.Field()
    url = scrapy.Field()
    sources = scrapy.Field()
