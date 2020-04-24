import os

from scrapy import cmdline

from weibo_spider.spiders import weibo_redis

def main():
    spider_path = os.path.abspath(weibo_redis.__file__)
    subject = '美国'
    cmdline.execute(['scrapy', 'runspider', spider_path, '-a', f'subject={subject}'])

if __name__ == '__main__':
    main()