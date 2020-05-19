import importlib
import os
from scrapy.crawler import CrawlerProcess
import importlib.util
import argparse
import sys

os.makedirs("script", exist_ok=True)

sys.path.append(os.path.abspath('.'))
if hasattr(sys, '_MEIPASS'):
    sys.path.append(sys._MEIPASS)

parser = argparse.ArgumentParser()
parser.add_argument('--script')
args = parser.parse_args()
script_name = args.script
# script_name = "pixiv.author"
# script_name = "pixiv.search"
_spac = ".%s" % script_name
try:
    script_spec = importlib.util.find_spec(_spac, package="script")
except ModuleNotFoundError:
    print("脚本 :%s 不存在请检查script目录" % script_name)
    sys.exit()

if script_name is None:
    print("需要使用 --script 指定至少一个存在于script的脚本名")
    sys.exit()

if script_spec is None:
    print("脚本 :%s 不存在请检查script目录" % script_name)
    sys.exit()

_import = importlib.import_module(script_spec.name, package="script")

if hasattr(_import, '__script__') is False:
    print("脚本 :%s 不存 '__script__' 指定入口" % script_name)
    sys.exit()

process = CrawlerProcess(_import.__script__.settings())
process.crawl(_import.__script__)
process.start()
