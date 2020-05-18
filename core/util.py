# -*- coding: UTF-8 -*-
import sys
import inspect
from tinydb import TinyDB
import os
from urllib import parse
from tinydb.storages import JSONStorage
from tinydb.middlewares import CachingMiddleware


def db_space(name) -> TinyDB:
    os.makedirs(os.path.dirname(name), exist_ok=True)
    return TinyDB(name, ensure_ascii=False, encoding="utf-8")


def list_chunks(list_data, size):
    for index in range(0, len(list_data), size):
        yield list_data[index:index + size]


def path_format(path: str):
    r_dir_filter = [
        ('/', '_'),
        ('\\', '_'),
        (':', '：'),
        ('*', '_'),
        ('?', u'？'),
        ('"', '_'),
        ('<', '['),
        ('>', ']'),
        ('|', '_'),
    ]
    for filter_ele in r_dir_filter:
        path = path.replace(filter_ele[0], filter_ele[1])
    return path


def url_query(url):
    return dict(parse.parse_qsl(parse.urlparse(url).query))


def package(name, path):
    _package = sys.modules[name].__package__
    return '%s.%s' % (_package, path)
