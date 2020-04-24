import requests
import json
import warnings
import time
import threading
import math

import pandas as pd
import pymongo
import pyecharts.options as opts
from pyecharts.charts import WordCloud
from scrapy.utils.project import get_project_settings

from data_analysis.config import API_KEY, SECRET_KEY

df_words = None


def get_df_words(access_token, data):
    headers = {
        'content-type': 'application/json'
    }
    url_lexer = f'https://aip.baidubce.com/rpc/2.0/nlp/v1/lexer?charset=UTF-8&access_token={access_token}'
    for i in data:
        try:
            response = requests.post(url=url_lexer, headers=headers, json={'text': i['news'].replace('小猪', '罗志祥')})
            if response:
                result = response.json()
                # 数据提取
                df_word = pd.DataFrame(result['items'])[['item', 'pos', 'ne']]
                # 提取所有名词+人名 - 多条件，并集
                df_word = df_word[(df_word['pos'] == 'n') | (df_word['ne'] == 'PER')]
                print('获取数据 >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>')
                global df_words
                df_words = pd.concat([df_words, df_word])
            else:
                print(response.json())
        except:
            continue
        # 百度免费的QPS为2, 所以作延迟处理
        time.sleep(0.5)

class CloudGraph(object):

    def __init__(self):
        self.API_KEY = API_KEY
        self.SECRET_KEY = SECRET_KEY
        settings = get_project_settings()
        config = settings['MONGO_CONFIG']
        conn = pymongo.MongoClient(
            host=config['host'],
            port=config['port'],
            connect=False
        )
        # 选择数据库
        self.db = conn.spiderinfo

    def get_token(self):
        host = f'https://aip.baidubce.com/oauth/2.0/token?grant_type=client_credentials&client_id={self.API_KEY}&client_secret={self.SECRET_KEY}'
        response = requests.get(host)
        if response:
            self.access_token = response.json()['access_token']
        else:
            self.access_token = None

    def parse_data(self, collection):
        data = self.db[collection].find({}, {'_id': 0, 'news': 1})
        count = data.count()
        return data, count


    def write_cloud(self, words_count, title, render_name):
        data_pair = []
        for i in range(words_count.count()):
            data_pair.append((words_count.index[i], str(words_count.values[i])))
        c = (
            WordCloud()
            .add(
                series_name='词频',
                data_pair=data_pair,
                shape='circle',
                word_size_range=[20, 100],
                rotate_step=10,
            )
            .set_global_opts(title_opts=opts.TitleOpts(title=title))
            .render(render_name)
        )


if __name__ == '__main__':
    # 创建队列
    cg = CloudGraph()
    cg.get_token()
    data_lzx, count_lzx = cg.parse_data(collection='weibo:lzx')
    record = []
    for i in range(5):
        t = threading.Thread(target=get_df_words, args=(cg.access_token, data_lzx))
        t.start()
        record.append(t)
        time.sleep(0.1)
    for t in record:
        t.join()
    df_words_count = df_words['item'].value_counts()
    cg.write_cloud(df_words_count, title='罗志祥——词云图', render_name='render_cloud.html')