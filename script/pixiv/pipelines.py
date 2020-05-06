# -*- mode: python -*-
from scrapy.pipelines.files import FileException, FilesPipeline
from scrapy.http.response.html import HtmlResponse
from scrapy import Spider, Request, FormRequest
import os
from core.util import path_format
import demjson
from .items import AuthorItem, TaskItem, SourceItem, TaskNovelItem, TaskMetaItem
from scrapy.pipelines.media import MediaPipeline
from ..pixiv import novel_format, novel_bind_image, novel_html


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
            self.file_space(item),
            resource.split('/')[-1]
        )
        return resource_path

    def file_space(self, item):
        author_path = "%s_%s" % (item['author']['name'], item['author']['id'])
        illust_path = "%s_%s" % (item['title'], item['id'])
        return os.path.join(
            path_format(author_path),
            path_format(illust_path),
        )

    def item_completed(self, results, item, info: MediaPipeline.SpiderInfo):
        space = info.spider.settings.get('FILES_STORE')
        _item_space = os.path.join(space, self.file_space(item))
        os.makedirs(_item_space, exist_ok=True)
        donwalod_space = os.path.join(_item_space, 'illust.json')
        _meta = TaskMetaItem(item)
        with open(donwalod_space, 'wb') as meta:
            meta.write(demjson.encode(dict(_meta), encoding="utf-8", compactly=False, indent_amount=4))

        if isinstance(item, TaskNovelItem):
            content = os.path.join(_item_space, 'novel.html')
            with open(content, 'w', encoding='utf-8') as meta:
                meta.write(novel_html(item['title'], item['content']))

        info.spider.spider_log.info("Complate : %s-%s-%s" % (item['title'], item['id'], donwalod_space), )
