import importlib
import os
from scrapy.crawler import CrawlerProcess
import importlib.util
import argparse
import sys

sys.path.append(os.path.abspath('.'))
# # parser = argparse.ArgumentParser()
# # parser.add_argument('--script')
# # args = parser.parse_args()
# # script_path = args.script
# # if script_path is None:
# #     print("需要使用 --script 载入至少一个脚本")
# #     sys.exit()
# #
# # if os.path.isfile(script_path) is False:
# #     print("%s 不存在" % os.path.abspath(script_path))
#
#
# script_path = os.path.join("script", "pixiv")
# _import = importlib.import_module("")

_name = ".pixiv.author"

_import = importlib.import_module(_name, package='script')

if hasattr(_import, '__script__') is False:
    pass

process = CrawlerProcess(_import.__script__.settings())
process.crawl(_import.__script__)
process.start()

# test_spec = importlib.util.spec_from_file_location("Test",
# loader = importlib.machinery.SourceFileLoader("script", script_path)
# loader.exec_module()
# # print(loader.is_package('author.py'))
# # module = loader.load_module()
# #
# # print(module)
#
# # process = CrawlerProcess(module.Script.settings())
# # process.crawl(module.Script)
# # process.start()
