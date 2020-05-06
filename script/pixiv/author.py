from core import CoreSpider
from scrapy import Spider, Request, FormRequest
from scrapy.http.response.html import HtmlResponse
from urllib.parse import urlparse, parse_qs, urlencode
import demjson
from core.runtime import Setting
from core.util import list_chunks, package
from .items import AuthorItem, TaskItem, SourceItem, TaskNovelItem
import sys
import os
import argparse
import re
from ..pixiv import novel_format, novel_bind_image, novel_html


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

    @classmethod
    def start_requests(cls):
        # _url = 'https://www.pixiv.net/users/6916534'
        _url = 'https://www.pixiv.net/users/24414324'
        # _url = 'https://www.pixiv.net/users/14284592'

        _cookies = Setting.space(cls.script_name()).parameter("cookies.json").json()
        cls.spider_log.info("Start Url : %s" % _url)
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/81.0.4044.122 Safari/537.36',
            'Accept-Language': 'zh-CN',
        }
        cls.spider_log.info("Use Headers : %s" % headers)
        yield Request(url=_url, callback=cls.analysis, headers=headers, cookies=_cookies)

    @classmethod
    def analysis(cls, response: HtmlResponse):
        url = urlparse(response.url)
        id = url.path.replace('/users/', '')
        cls.spider_log.info("Author Id : %s" % id)
        data_all = 'https://www.pixiv.net/ajax/user/%s/profile/all' % id
        cls.spider_log.info("Item Url  : %s" % data_all)
        yield Request(url=data_all, callback=cls.illusts, meta={
            'id': id
        })

    @classmethod
    def illusts(cls, response: HtmlResponse):
        _detail = demjson.decode(response.text)

        illusts = []
        mangas = []
        novels = []
        if len(_detail['body']['illusts']) > 0:
            illusts = _detail['body']['illusts'].keys()
        if len(_detail['body']['manga']) > 0:
            mangas = _detail['body']['manga'].keys()
        if len(_detail['body']['novels']) > 0:
            novels = _detail['body']['novels'].keys()
        cls.spider_log.info("Illusts    Total :%s" % len(illusts))
        cls.spider_log.info("Mangas     Total :%s" % len(mangas))
        cls.spider_log.info("Novels     Total :%s" % len(novels))
        cls.spider_log.info("ALL        Total :%s" % (len(illusts) + len(mangas) + len(novels)))

        for illust_indexs in list_chunks(list(illusts), 48):
            params = {
                'ids[]': illust_indexs,
                'work_category': 'illust',
                'is_first_page': 0
            }
            illusts_meta = 'https://www.pixiv.net/ajax/user/%s/profile/illusts?%s' % (
                response.meta['id'],
                urlencode(params, True)
            )
            yield Request(url=illusts_meta, callback=cls.illusts_metas, meta=response.meta)

        for manga_indexs in list_chunks(list(mangas), 48):
            params = {
                'ids[]': manga_indexs,
                'work_category': 'manga',
                'is_first_page': 0
            }
            illusts_meta = 'https://www.pixiv.net/ajax/user/%s/profile/illusts?%s' % (
                response.meta['id'],
                urlencode(params, True)
            )
            yield Request(url=illusts_meta, callback=cls.illusts_metas, meta=response.meta)

        for novel_indexs in novels:
            novel_url = 'https://www.pixiv.net/ajax/novel/%s' % novel_indexs
            response.meta['id'] = novel_indexs
            yield Request(url=novel_url, callback=cls.novels_metas, meta=response.meta)

    @classmethod
    def novels_metas(cls, response: HtmlResponse):
        # 67152702-1
        _novel_meta = demjson.decode(response.text)['body']

        author_item = AuthorItem()
        author_item['id'] = _novel_meta['userId']
        author_item['name'] = _novel_meta['userName']
        #
        task_item = TaskNovelItem()
        task_item['id'] = _novel_meta['id']
        task_item['title'] = _novel_meta['title']
        task_item['description'] = _novel_meta['description']
        task_item['author'] = author_item
        task_item['content'] = novel_format(_novel_meta['content'])
        # novel_format, novel_bind_image
        source_item = SourceItem()
        source_item['type'] = 'novel'
        source_item['url'] = response.url
        source_item['sources'] = [
            _novel_meta['coverUrl']
        ]
        task_item['source'] = source_item

        _search_pixiv_images = re.search(r'\[pixivimage:(.*?)\]', _novel_meta['content'], re.M | re.I)
        if _search_pixiv_images is not None:
            params = {
                'id[]': _search_pixiv_images.groups(),
                'lang': 'zh'
            }
            pixivimage_meta = 'https://www.pixiv.net/ajax/novel/%s/insert_illusts?%s' % (
                _novel_meta['id'],
                urlencode(params, True)
            )
            headers = {
                'referer': 'https://www.pixiv.net/novel/show.php?id=%s' % _novel_meta['id']
            }
            response.meta['item'] = task_item
            yield Request(url=pixivimage_meta, callback=cls.novels_detail, meta=response.meta, headers=headers)
        else:
            yield task_item

    @classmethod
    def novels_detail(cls, response: HtmlResponse):
        _novel_meta = demjson.decode(response.text)['body']
        task_item = response.meta['item']
        _bind_images = {}
        for id, _detail in _novel_meta.items():
            _bind_images[id] = _detail['illust']['images']['original'].split('/')[-1]
            task_item['source']['sources'].append(_detail['illust']['images']['original'])
        task_item['content'] = novel_bind_image(task_item['content'], _bind_images)
        yield task_item

    @classmethod
    def illusts_metas(cls, response: HtmlResponse):
        illusts_meta = demjson.decode(response.text)['body']['works']

        for illust_meta in illusts_meta.values():
            artworks = 'https://www.pixiv.net/ajax/illust/%s' % illust_meta['illustId']
            referer = 'https://www.pixiv.net/artworks/%s' % illust_meta['illustId']
            cls.spider_log.info("Illust Title :%s" % illust_meta['illustTitle'])
            yield Request(url=artworks, callback=cls.illust_detail, meta=response.meta, headers={
                'Referer': referer
            })

    @classmethod
    def illust_detail(cls, response: HtmlResponse):
        illust_detail = demjson.decode(response.text)

        task_item = TaskItem()
        task_item['id'] = illust_detail['body']['illustId']
        task_item['title'] = illust_detail['body']['illustTitle']
        task_item['description'] = illust_detail['body']['description']
        task_item['tags'] = [
            tag['tag']
            for tag in illust_detail['body']['tags']['tags']
        ]

        author_item = AuthorItem()
        author_item['id'] = illust_detail['body']['userId']
        author_item['name'] = illust_detail['body']['userName']

        task_item['author'] = author_item
        source_item = SourceItem()
        task_item['source'] = source_item
        response.meta['task'] = task_item
        if illust_detail['body']['illustType'] == 2:
            source_item['type'] = 'ugoira'
            source_item['url'] = 'https://www.pixiv.net/ajax/illust/%s/ugoira_meta' % illust_detail['body']['illustId']
            yield Request(url=source_item['url'], meta=response.meta, callback=cls.ugoira_source)

        if illust_detail['body']['illustType'] != 2:
            source_item['type'] = 'page'
            source_item['url'] = 'https://www.pixiv.net/ajax/illust/%s/pages' % illust_detail['body']['illustId']
            yield Request(url=source_item['url'], meta=response.meta, callback=cls.page_source)

    @classmethod
    def page_source(cls, response: HtmlResponse):
        source_data = demjson.decode(response.text)['body']
        sources = [data['urls']['original'] for data in source_data]
        item = response.meta['task']
        item['source']['sources'] = sources
        yield item

    @classmethod
    def ugoira_source(cls, response: HtmlResponse):
        source_data = demjson.decode(response.text)['body']
        item = response.meta['task']
        item['source']['sources'] = [
            source_data['originalSrc'],
            source_data['src']
        ]
        yield item


__script__ = Script
