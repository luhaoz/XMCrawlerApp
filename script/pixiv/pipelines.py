# -*- mode: python -*-
from scrapy.pipelines.files import FileException, FilesPipeline
from scrapy.http.response.html import HtmlResponse
from scrapy import Spider, Request, FormRequest
import os
from core.util import path_format
import demjson
from .items import AuthorItem, TaskItem, SourceItem

from scrapy.pipelines.media import MediaPipeline


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

        author_path = "%s_%s" % (item['author']['name'], item['author']['id'])
        illust_path = "%s_%s" % (item['title'], item['id'])

        resource_path = os.path.join(
            path_format(author_path),
            path_format(illust_path),
            resource.split('/')[-1]
        )
        return resource_path

    def item_completed(self, results, item, info: MediaPipeline.SpiderInfo):

        donwalod = results[0]
        if donwalod[0]:
            space = info.spider.settings.get('FILES_STORE')
            path = donwalod[1]['path']
            donwalod_space = os.path.join(space, os.path.dirname(path), 'illust.json')
            with open(donwalod_space, 'wb') as meta:
                meta.write(demjson.encode(dict(item), encoding="utf-8", compactly=False, indent_amount=4))

        info.spider.spider_log.info("Complate : %s-%s-%s" % (item['title'], item['id'], donwalod_space), )
