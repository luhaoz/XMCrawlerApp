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
from ..pixiv import novel_format, novel_bind_image, novel_html, author_space, artworks, file_space
from core.util import path_format, db_space
from tinydb import Query


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
            'FILES_STORE': 'E:\\MegaSync\\pixiv\\author',
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
        urls = [
            'https://www.pixiv.net/users/45847523',
            'https://www.pixiv.net/users/28617557',
            'https://www.pixiv.net/users/6916534',
            'https://www.pixiv.net/users/471249',
            'https://www.pixiv.net/users/24414324',
            'https://www.pixiv.net/users/687125',
            'https://www.pixiv.net/users/15436076',
            'https://www.pixiv.net/users/14440528',
            'https://www.pixiv.net/users/8969258',
            'https://www.pixiv.net/users/17801188',
            'https://www.pixiv.net/users/45847523',
            'https://www.pixiv.net/users/11022194',
            'https://www.pixiv.net/users/18261283',
            'https://www.pixiv.net/users/26495687',
            'https://www.pixiv.net/users/8587823',
        ]
        _cookies = Setting.space(cls.script_name()).parameter("cookies.json").json()
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/81.0.4044.122 Safari/537.36',
            'Accept-Language': 'zh-CN',
        }
        cls.spider_log.info("Use Headers : %s" % headers)
        for _url in urls:
            cls.spider_log.info("Start Url : %s" % _url)
            yield Request(url=_url, callback=cls.analysis, headers=headers, cookies=_cookies)

    @classmethod
    def analysis(cls, response: HtmlResponse):
        url = urlparse(response.url)
        id = url.path.replace('/users/', '')
        cls.spider_log.info("Author Id : %s" % id)
        data_all = 'https://www.pixiv.net/ajax/user/%s/profile/all' % id
        cls.spider_log.info("Item Url  : %s" % data_all)
        author_item = AuthorItem()
        _meta_content = response.xpath('//meta[@id="meta-preload-data"]/@content').extract_first()
        _meta = demjson.decode(_meta_content)
        author_item['id'] = _meta['user'][id]['userId']
        author_item['name'] = _meta['user'][id]['name']
        yield Request(url=data_all, callback=cls.illusts, meta={
            "id": id,
            "author": author_item
        })

    @classmethod
    def illusts(cls, response: HtmlResponse):
        _detail = demjson.decode(response.text)

        _cls = cls

        def _filter(id):
            _space = _cls.settings().get('FILES_STORE')
            _author_space = author_space({
                'author': response.meta['author']
            })
            _db = db_space(os.path.join(_space, _author_space, '%s_main.json' % cls.script_name()))
            _has = len(_db.search(Query().id == id)) > 0
            if _has is True:
                _cls.spider_log.info("Skip Item :%s" % str(id))
            return _has

        illusts = list(artworks(_detail['body']['illusts'], _filter))
        mangas = list(artworks(_detail['body']['manga'], _filter))
        novels = list(artworks(_detail['body']['novels'], _filter))

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
        task_item['space'] = file_space(task_item)
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
        task_item['upload_date'] = illust_detail['body']['uploadDate']
        task_item['tags'] = [
            tag['tag']
            for tag in illust_detail['body']['tags']['tags']
        ]

        author_item = response.meta['author']

        task_item['author'] = author_item
        source_item = SourceItem()
        task_item['source'] = source_item

        task_item['space'] = file_space(task_item)
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
