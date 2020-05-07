from scrapy import Spider, Request, FormRequest
import sys
from core.logging import logger
from logging import Logger
from pydispatch import dispatcher
from scrapy import signals
from core.util import path_format, db_space


class CoreSpider(Spider):
    spider_log: Logger = None
    __arguments = None

    def __init__(self):
        Spider.__init__(self, name=self.__class__.script_name())
        self.__class__.spider_log = logger(self.__class__.script_name())
        dispatcher.connect(self.spider_closed, signals.spider_closed)

    @classmethod
    def arguments(cls, parser):
        pass

    @classmethod
    def script_name(cls):
        return cls.__module__

    @classmethod
    def settings(cls):
        return {}

    def spider_closed(self, spider):
        self.__class__.spider_log.info("爬虫结束")
