from scrapy import Spider, Request, FormRequest
import sys
from core.logging import logger
from logging import Logger


class CoreSpider(Spider):
    spider_log: Logger = None

    def __init__(self):
        Spider.__init__(self, name=self.__class__.script_name())
        self.__class__.spider_log = logger(self.__class__.script_name())

    @classmethod
    def script_name(cls):
        _script_name_: str = sys.modules[cls.__module__].__file__
        return _script_name_.replace(".py", "").replace("\\", ".")

    @classmethod
    def settings(cls):
        return {}
