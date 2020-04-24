# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html
import json
import pymysql
import pymongo
import sys
import getopt

from scrapy.utils.project import get_project_settings

from weibo_spider.spiders.weibo_cookie import WeiboCookieSpider

class MySqlPipeline(object):

    def __init__(self):
        # 读取配置文件至内存中
        settings = get_project_settings()
        db = settings['MYSQL_CONFIG']
        # 连接数据库
        self.conn = pymysql.Connect(
            host=db['host'],
            port=db['port'],
            user=db['user'],
            password=db['password'],
            db=db['database'],
            charset=db['charset']
        )

    def process_item(self, item, spider):
        # 写入数据库
        sql = f'''insert into weibo_subject(`title`, `avatar`, `nickname`, `icon`, `news`, `time`, `origin`, `collect`, `forward`, `comment`, `like`) values("{item['title'] or ''}", "{item['avatar'] or ''}", "{item['nickname'] or ''}", "{item['icon'] or ''}", "{item['news'] or ''}", "{item['time'] or ''}", "{item['origin'] or ''}", {item['collect']}, {item['forward']}, {item['comment']}, {item['like']});'''
        # 执行sql语句
        self.cursor = self.conn.cursor()
        try:
            self.cursor.execute(sql)
            self.conn.commit()
        except Exception as e:
            print(e)
            self.conn.rollback()

        return item

    def close_spider(self, spider):
        self.cursor.close()
        self.conn.close()

class MyMongoPipeline(object):

    def open_spider(self, spider):
        # 连接数据库
        db_name = 'unknown'
        for arg in sys.argv:
            if 'dbName=' in arg:
                db_name = arg.replace('dbName=', '')
                break
        settings = get_project_settings()
        config = settings['MONGO_CONFIG']
        self.conn = pymongo.MongoClient(
            host=config['host'],
            port=config['port']
        )
        # 选择数据库，没有这个库会自动创建
        db = self.conn.spiderinfo
        # 选择集合
        self.collection = db[f'weibo:{db_name}']

    def process_item(self, item, spider):
        # 写入mongodb中
        self.collection.insert(dict(item))
        return item

    def close_spider(self, spider):
        self.conn.close()

class WeiboSpiderPipeline(object):

    def __init__(self):
        self.fp = open('weibo.txt', 'w', encoding='utf-8')

    def process_item(self, item, spider):
        dt = dict(item)
        self.fp.write(json.dumps(dt, ensure_ascii=False) + '\n')
        return item

    def close_spider(self, spider):
        self.fp.close()