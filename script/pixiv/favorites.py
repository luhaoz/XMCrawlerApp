from core import CoreSpider
from scrapy import Spider, Request, FormRequest
from scrapy.http.response.html import HtmlResponse
from urllib.parse import urlparse, parse_qs, urlencode
import demjson
from core.runtime import Setting
from core.util import list_chunks, package, url_query, db_space
from .items import AuthorItem, TaskItem, SourceItem, TaskNovelItem
import sys
import os
import argparse
from urllib.request import quote
import math
from ..pixiv import novel_format, novel_bind_image, novel_html, author_space, artworks, item_space
import re
from .databases.main import MainSpace


class Script(CoreSpider):

    @classmethod
    def settings(cls):
        return {
            'RETRY_ENABLED': True,
            'RETRY_TIMES': 10,
            'AUTOTHROTTLE_ENABLED': True,
            'CONCURRENT_REQUESTS': 24,
            'LOG_LEVEL': 'ERROR',
            'LOG_ENABLED': True,
            'FILES_STORE': 'space',
            'DOWNLOADER_MIDDLEWARES': {
                # 'script.pixiv.pipelines.ProxyPipeline': 350,
                # 'scrapy.downloadermiddlewares.httpproxy.HttpProxyMiddleware': 400,
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

        _space = cls.settings().get('FILES_STORE')
        _cookies = Setting.space(cls.script_name()).parameter("cookies.json").json()
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/81.0.4044.122 Safari/537.36',
            'Accept-Language': 'zh-CN',
        }
        _group = "favorites"
        _database = os.path.join(_space, _group, '%s_main.db' % cls.script_name())
        cls.space.set(_database, MainSpace.space(_database))

        _url = "https://www.pixiv.net/bookmark.php?rest=show&type=illust_all&p=588"
        yield Request(url=_url, callback=cls.favorites, headers=headers, cookies=_cookies, meta={
            'group': _group
        })

        # _url = "https://www.pixiv.net/novel/bookmark.php?type=all"
        # yield Request(url=_url, callback=cls.favorites_novels, headers=headers, cookies=_cookies, meta={
        #     'group': _group
        # })

    @classmethod
    def favorites(cls, response: HtmlResponse):
        # _total = int(response.xpath('//span[@class="count-badge"]/text()').extract_first().replace('件', ''))
        # _pages = math.ceil(_total / 20)
        _cls = cls
        _space = cls.settings().get('FILES_STORE')

        def _filter(id):
            _database = os.path.join(_space, response.meta['group'], '%s_main.db' % cls.script_name())
            cls.space.set(_database, MainSpace.space(_database))
            _has = _cls.space.get(_database).skip_complete({
                'id': id
            })
            if _has is True:
                _cls.spider_log.info("Skip Item :%s" % str(id))
            return _has

        _favorites = response.xpath('//li[@class="image-item"]')
        for _item in _favorites:

            _href = _item.xpath('./a/@href').extract_first()
            _id = _href.replace('/artworks/', '')

            _has_user = _item.xpath('./a[@data-user_id]').extract_first()
            if _has_user is None:
                continue
            #
            if _filter(_id) is True:
                continue

            _source = 'https://www.pixiv.net/ajax/illust/%s' % _id
            _artworks = 'https://www.pixiv.net%s' % _href
            yield Request(url=_source, callback=cls.illust_detail, headers={
                'referer': _artworks
            }, meta=response.meta)

        _has_next = response.xpath('//a[@rel="next"]/@href').extract_first()
        if _has_next is not None:
            _has_next_url = 'https://www.pixiv.net/bookmark.php%s' % _has_next
            yield Request(url=_has_next_url, callback=cls.favorites, meta=response.meta)

    @classmethod
    def favorites_novels(cls, response: HtmlResponse):

        _cls = cls
        _space = cls.settings().get('FILES_STORE')

        def _filter(id):
            _database = os.path.join(_space, response.meta['group'], '%s_main.db' % cls.script_name())
            cls.space.set(_database, MainSpace.space(_database))
            _has = _cls.space.get(_database).skip_complete({
                'id': id
            })
            if _has is True:
                _cls.spider_log.info("Skip Item :%s" % str(id))
            return _has

        _favorites = response.xpath('//div[@class="novel-right-contents"]//h1[@class="title"]')
        for _item in _favorites:
            _href = _item.xpath('./a/@href').extract_first()
            _query = url_query(_href)

            _has_user = _item.xpath('./a[@data-user_id]').extract_first()
            if _has_user is None:
                continue

            if _filter(_query['id']) is True:
                continue

            _source = 'https://www.pixiv.net/ajax/novel/%s' % _query['id']
            _artworks = ' https://www.pixiv.net/novel/show.php?id=%s' % _query['id']
            yield Request(url=_source, callback=cls.novels_metas, headers={
                'referer': _artworks
            }, meta=response.meta)

        _has_next = response.xpath('//a[@rel="next"]/@href').extract_first()
        if _has_next is not None:
            _has_next_url = 'https://www.pixiv.net/novel/bookmark.php%s' % _has_next
            yield Request(url=_has_next_url, callback=cls.favorites, meta=response.meta)

    @classmethod
    def novels_metas(cls, response: HtmlResponse):
        _novel_meta = demjson.decode(response.text)['body']

        author_item = AuthorItem()
        author_item['id'] = _novel_meta['userId']
        author_item['name'] = _novel_meta['userName']

        task_item = TaskNovelItem()
        task_item['id'] = _novel_meta['id']
        task_item['title'] = _novel_meta['title']
        task_item['description'] = _novel_meta['description']
        task_item['author'] = author_item
        task_item['content'] = novel_format(_novel_meta['content'])
        task_item['upload_date'] = _novel_meta['uploadDate']
        task_item['count'] = 1
        task_item['type'] = 'novel'
        task_item['tags'] = [
            tag['tag']
            for tag in _novel_meta['tags']['tags']
        ]

        source_item = SourceItem()
        source_item['type'] = 'novel'
        source_item['url'] = response.url
        source_item['sources'] = [
            _novel_meta['coverUrl']
        ]
        task_item['source'] = source_item
        task_item['space'] = os.path.join(response.meta['group'], item_space(task_item))
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
        task_item['count'] = illust_detail['body']['pageCount']
        task_item['upload_date'] = illust_detail['body']['uploadDate']
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
        task_item['space'] = os.path.join(response.meta['group'], item_space(task_item))
        response.meta['task'] = task_item

        if illust_detail['body']['illustType'] == 2:
            task_item['type'] = 'ugoira'
            source_item['type'] = 'ugoira'
            source_item['url'] = 'https://www.pixiv.net/ajax/illust/%s/ugoira_meta' % illust_detail['body']['illustId']
            yield Request(url=source_item['url'], meta=response.meta, callback=cls.ugoira_source)

        if illust_detail['body']['illustType'] != 2:
            task_item['type'] = 'illust'
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
