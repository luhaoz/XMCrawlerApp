# -*- mode: python -*-
from scrapy.pipelines.files import FileException, FilesPipeline
from scrapy.http.response.html import HtmlResponse
from scrapy import Spider, Request, FormRequest
import os
from core.util import path_format, db_space
import demjson
from .items import AuthorItem, TaskItem, SourceItem, TaskNovelItem, TaskMetaItem
from scrapy.pipelines.media import MediaPipeline
from ..pixiv import novel_format, novel_bind_image, novel_html, author_space, file_space
from tinydb import Query


class ProxyPipeline(object):
    def process_request(self, request, spider):
        request.meta['proxy'] = "http://127.0.0.1:10809"


class TaskPipeline(FilesPipeline):

    def get_media_requests(self, item: TaskItem, info: MediaPipeline.SpiderInfo):
        spider = info.spider
        spider.spider_log.info("Item : %s" % item)

        for resource in item['source']['sources']:
            yield Request(resource, meta={
                'item': item,
                'resource': resource
            }, headers={
                'Referer': 'https://www.pixiv.net/artworks/%s' % item['id']
            })

    def file_path(self, request, response=None, info=None):
        item = request.meta['item']
        resource = request.meta['resource']
        resource_path = os.path.join(
            file_space(item),
            resource.split('/')[-1]
        )
        return resource_path

    def item_completed(self, results, item, info: MediaPipeline.SpiderInfo):
        space = info.spider.settings.get('FILES_STORE')
        _item_space = os.path.join(space, file_space(item))
        _author_space = os.path.join(space, author_space(item))
        _db = db_space(os.path.join(_author_space, '%s_main.json' % info.spider.__class__.script_name()))
        os.makedirs(_item_space, exist_ok=True)
        donwalod_space = os.path.join(_item_space, 'illust.json')
        _meta = TaskMetaItem(item)
        with open(donwalod_space, 'wb') as meta:
            meta.write(demjson.encode(dict(_meta), encoding="utf-8", compactly=False, indent_amount=4))

        if isinstance(item, TaskNovelItem):
            content = os.path.join(_item_space, 'novel.html')
            with open(content, 'w', encoding='utf-8') as meta:
                meta.write(novel_html(item['title'], item['content']))

        if len(_db.search(Query().id == item['id'])) <= 0:
            _db.insert(demjson.decode(demjson.encode(_meta, encoding="utf-8"), encoding="utf-8"))
        info.spider.spider_log.info("Complate : %s-%s-%s" % (item['title'], item['id'], donwalod_space), )
