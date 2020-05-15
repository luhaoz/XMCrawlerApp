# -*- mode: python -*-
from scrapy.pipelines.files import FileException, FilesPipeline
from scrapy.http.response.html import HtmlResponse
from scrapy import Spider, Request, FormRequest
import os
from core.util import path_format, db_space
import demjson
from .items import AuthorItem, TaskItem, SourceItem, TaskNovelItem, TaskMetaItem, TaskMetaResultItem
from scrapy.pipelines.media import MediaPipeline
from ..pixiv import novel_format, novel_bind_image, novel_html, author_space, file_space
from tinydb import Query
from scrapy.exceptions import DropItem


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
            item['space'],
            resource.split('/')[-1]
        )
        return resource_path

    def item_completed(self, results, item, info: MediaPipeline.SpiderInfo):
        # print(results)

        for ok, result in results:
            if ok is False:
                info.spider.spider_log.error("Error : %s-%s" % (item['title'], item['id']))
                raise DropItem("Error : %s-%s" % (item['title'], item['id']))

        space = info.spider.settings.get('FILES_STORE')

        _root_space = os.path.dirname(item['space'])
        _db = db_space(os.path.join(space, _root_space, '%s_main.json' % info.spider.__class__.script_name()))
        os.makedirs(os.path.join(space, item['space']), exist_ok=True)
        donwalod_space = os.path.join(space, item['space'], 'illust.json')

        _meta = TaskMetaResultItem(item)
        _meta['results'] = [
            _result for _ok, _result in results
        ]
        with open(donwalod_space, 'wb') as meta:
            meta.write(demjson.encode(dict(_meta), encoding="utf-8", compactly=False, indent_amount=4))

        if isinstance(item, TaskNovelItem):
            content = os.path.join(space, item['space'], 'novel.html')
            with open(content, 'w', encoding='utf-8') as meta:
                meta.write(novel_html(item['title'], item['content']))

        if len(_db.search(Query().id == item['id'])) <= 0:
            _db.insert(demjson.decode(demjson.encode(_meta, encoding="utf-8"), encoding="utf-8"))

        info.spider.spider_log.info("Complate : %s-%s-%s" % (item['title'], item['id'], donwalod_space))
