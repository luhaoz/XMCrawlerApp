from core import CoreSpider
from scrapy import Spider, Request, FormRequest
from scrapy.http.response.html import HtmlResponse
from urllib.parse import urlparse, parse_qs, urlencode
import demjson
from core.runtime import Setting
from core.util import list_chunks, package
import sys
import os
import argparse
import re


class Script(CoreSpider):

    @classmethod
    def arguments(cls, parser):
        pass
        # parser = argparse.ArgumentParser()
        # parser.add_argument('--id')
        # args = parser.parse_args()
        # if args.id is None:
        #     print("需要使用 --id 指定至少一个Pixiv 作者id")
        #     sys.exit()
        # print(args.id)

    @classmethod
    def settings(cls):
        return {
            'AUTOTHROTTLE_ENABLED': True,
            'CONCURRENT_REQUESTS': 24,
            'LOG_LEVEL': 'ERROR',
            'LOG_ENABLED': True,
            'FILES_STORE': 'space',
            'DOWNLOADER_MIDDLEWARES': {
                'script.pixiv.pipelines.ProxyPipeline': 350,
                'scrapy.downloadermiddlewares.httpproxy.HttpProxyMiddleware': 400,
                # 'app.pixiv.core.pipelines.DuplicatesPipeline': 90
                # 'scrapy.downloadermiddlewares.httpproxy.HttpProxyMiddleware': 1,
                # 'app.pixiv.pipelines.HttpbinProxyMiddleware': 2,
            },
            'ITEM_PIPELINES': {
                'script.pixiv.pipelines.TaskPipeline': 90
            },
        }

    # https://www.deviantart.com/_napi/da-user-profile/api/gallery/contents?username=Blacksword03&offset=0&limit=24&all_folder=true&mode=newest
    @classmethod
    def start_requests(cls):
        urls = [
            'https://www.deviantart.com/blacksword03'
        ]
        _cookies = Setting.space(cls.script_name()).parameter("cookies.json").json()
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/81.0.4044.122 Safari/537.36',
            'Accept-Language': 'zh-CN',
        }
        cls.spider_log.info("Use Headers : %s" % headers)
        for _url in urls:
            cls.spider_log.info("Start Url : %s" % _url)
            url = urlparse(_url)
            username = url.path[1:]
            _start_url = 'https://www.deviantart.com/_napi/da-user-profile/api/gallery/contents?username=%s&offset=0&limit=24&all_folder=true&mode=newest' % username
            yield Request(url=_start_url, callback=cls.analysis, headers=headers, cookies=_cookies, meta={
                'username': username
            })

    @classmethod
    def analysis(cls, response: HtmlResponse):
        username = response.meta['username']
        _result = demjson.decode(response.text)
        print(_result)
        # _author = _result['']

        _next_url = 'https://www.deviantart.com/_napi/da-user-profile/api/gallery/contents?username=%s&offset=%s&limit=24&all_folder=true&mode=newest' % (username, _result['nextOffset'])
        for deviation in _result['results']:
            _deviation = deviation['deviation']
            # print(_deviation['url'])
            response.meta['deviation'] = _deviation
            _url = 'https://www.deviantart.com/blacksword03/art/Prime2-840220579'
            # yield Request(url=_deviation['url'], callback=cls.gallery, meta=response.meta)
            yield Request(url=_url, callback=cls.gallery, meta=response.meta)
            break
        # if _result['hasMore'] is True:
        #     yield Request(url=_next_url, callback=cls.analysis, meta=response.meta)

    @classmethod
    def gallery(cls, response: HtmlResponse):
        print(response.text)
        _search_detail = re.search(r' window\.__INITIAL_STATE__ = JSON\.parse\((.*)\)', response.text, re.M | re.I)
        _data_json_string = _search_detail.groups()[0]
        print(demjson.decode(_data_json_string))


__script__ = Script
