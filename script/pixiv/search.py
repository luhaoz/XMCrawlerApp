from core import CoreSpider
from scrapy import Spider, Request, FormRequest
from scrapy.http.response.html import HtmlResponse
from urllib.parse import urlparse, parse_qs, urlencode
import demjson
from core.runtime import Setting
from core.util import list_chunks, package, url_query
from .items import AuthorItem, TaskItem, SourceItem, TaskNovelItem
import sys
import os
import argparse
from urllib.request import quote
import math
from ..pixiv import novel_format, novel_bind_image, novel_html, author_space, artworks, item_space
import re


class Script(CoreSpider):

    @classmethod
    def settings(cls):
        return {
            'AUTOTHROTTLE_ENABLED': True,
            'CONCURRENT_REQUESTS': 24,
            # 'LOG_LEVEL': 'ERROR',
            # 'LOG_ENABLED': True,
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

        _tags = [
            '巨大ヒロイン'
        ]

        _cookies = Setting.space(cls.script_name()).parameter("cookies.json").json()
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/81.0.4044.122 Safari/537.36',
            'Accept-Language': 'zh-CN',
        }
        for tag in _tags:
            pass

            item_types = [
                {
                    "url": "illustrations",
                    "type": "illust",
                    "page_count": 60,
                },
                {
                    "url": "manga",
                    "type": "manga",
                    "page_count": 60,
                },
                {
                    "url": "novels",
                    "type": "novel",
                    "page_count": 24,
                }
            ]

            for _item_type in item_types:
                _item_url = "https://www.pixiv.net/ajax/search/%s/%s?word=%s&order=date_d&mode=all&p=1&s_mode=s_tag_full&lang=zh" % (_item_type['url'], tag, tag)
                cls.spider_log.info("Start Url %s: %s" % (_item_type, _item_url))
                yield Request(url=_item_url, callback=cls.page, headers=headers, cookies=_cookies, meta={
                    "item_type": _item_type,
                })

    @classmethod
    def page(cls, response: HtmlResponse):

        current = url_query(response.url)
        current_page = int(current['p'])
        tag = current['word']
        item_type = response.meta['item_type']
        _search = demjson.decode(response.text)['body'][item_type['type']]
        _pages = math.ceil(_search['total'] / item_type['page_count'])
        cls.spider_log.info("Search :%s Type:%s Total :%s Pages: %s Current :%s" % (tag, item_type['type'], _search['total'], _pages, current_page))

        # datas
        _datas = _search['data']
        response.meta['word'] = tag
        for _data in _datas:
            if item_type['type'] in ['manga', 'illust']:
                artworks = "https://www.pixiv.net/ajax/illust/%s" % _data['id']
                referer = 'https://www.pixiv.net/artworks/%s' % _data['id']
                cls.spider_log.info("Illust Title :%s" % _data['title'])
                author_item = AuthorItem()

                author_item['id'] = _data['userId']
                author_item['name'] = _data['userName']

                response.meta['author'] = author_item
                yield Request(url=artworks, callback=cls.illust_detail, meta=response.meta, headers={
                    'Referer': referer
                })
                break

            if item_type['type'] in ['novel']:
                _novel_url = "https://www.pixiv.net/ajax/novel/%s" % _data['id']
                cls.spider_log.info("Novel Title :%s" % _data['title'])
                author_item = AuthorItem()
                author_item['id'] = _data['userId']
                author_item['name'] = _data['userName']
                response.meta['author'] = author_item
                yield Request(url=_novel_url, callback=cls.novels_metas, meta=response.meta)
                break

        if current_page < _pages:
            _item_url = "https://www.pixiv.net/ajax/search/%s/%s?word=%s&order=date_d&mode=all&p=%s&s_mode=s_tag_full&lang=zh" % (item_type['url'], tag, tag, current_page + 1)
            # yield Request(url=_item_url, callback=cls.page, meta=response.meta)

    @classmethod
    def novels_metas(cls, response: HtmlResponse):
        _novel_meta = demjson.decode(response.text)['body']

        author_item = response.meta['author']

        task_item = TaskNovelItem()
        task_item['id'] = _novel_meta['id']
        task_item['title'] = _novel_meta['title']
        task_item['description'] = _novel_meta['description']
        task_item['author'] = author_item
        task_item['content'] = novel_format(_novel_meta['content'])
        task_item['upload_date'] = _novel_meta['uploadDate']

        source_item = SourceItem()
        source_item['type'] = 'novel'
        source_item['url'] = response.url
        source_item['sources'] = [
            _novel_meta['coverUrl']
        ]
        task_item['source'] = source_item
        task_item['space'] = os.path.join(response.meta['word'], item_space(task_item))
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
            if _detail['illust'] is not None:
                _bind_images[id] = _detail['illust']['images']['original'].split('/')[-1]
                task_item['source']['sources'].append(_detail['illust']['images']['original'])
        task_item['content'] = novel_bind_image(task_item['content'], _bind_images)
        yield task_item

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
        task_item['space'] = os.path.join(response.meta['word'], item_space(task_item))
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
