from core import CoreSpider
from scrapy import Spider, Request, FormRequest
from scrapy.http.response.html import HtmlResponse
from urllib.parse import urlparse, parse_qs, urlencode
import demjson

class Script(CoreSpider):

    @classmethod
    def settings(cls):
        return {
            'AUTOTHROTTLE_ENABLED': True,
            'CONCURRENT_REQUESTS': 24,
            'LOG_LEVEL': 'ERROR',
            'LOG_ENABLED': True
        }

    @classmethod
    def start_requests(cls):
        _url = 'https://www.pixiv.net/users/471249'
        cls.spider_log.info("Start Url : %s" % _url)
        yield Request(url=_url, callback=cls.analysis)

    @classmethod
    def analysis(cls, response: HtmlResponse):
        url = urlparse(response.url)
        id = url.path.replace('/users/', '')
        data_all = 'https://www.pixiv.net/ajax/user/%s/profile/all' % id
        print(data_all)

    @classmethod
    def illusts(cls, response: HtmlResponse):
        illusts = demjson.decode(response.text)['body']['illusts']
        illusts_ids = [id for id in illusts.keys()]
        for illust_index in range(0, len(illusts_ids), 48):
            illusts_ids_group = illusts_ids[illust_index:illust_index + 48]
            # print(illusts_ids_group)
            params = {
                'ids[]': illusts_ids_group,
                'work_category': 'illust',
                'is_first_page': 0
            }
            illusts_meta = 'https://www.pixiv.net/ajax/user/%s/profile/illusts?%s' % (
                response.meta['id'],
                urlencode(params, True)
            )
            yield Request(url=illusts_meta, callback=cls.illusts_meta, meta=response.meta)