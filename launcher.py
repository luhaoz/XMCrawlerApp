import importlib
import os
from scrapy.crawler import CrawlerProcess
import importlib.machinery
import argparse
import sys

# parser = argparse.ArgumentParser()
# parser.add_argument('--script')
# args = parser.parse_args()
# script_path = args.script
# if script_path is None:
#     print("需要使用 --script 载入至少一个脚本")
#     sys.exit()
#
# if os.path.isfile(script_path) is False:
#     print("%s 不存在" % os.path.abspath(script_path))


script_path = os.path.join("script", "pixiv", 'author.py')

loader = importlib.machinery.SourceFileLoader("script", script_path)
module = loader.load_module()

process = CrawlerProcess(module.Script.settings())
process.crawl(module.Script)
process.start()
