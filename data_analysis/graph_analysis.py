import requests
import json
import warnings
import time
import threading
import math

import pandas as pd
import pymongo
import pyecharts.options as opts
from pyecharts.charts import Graph
from scrapy.utils.project import get_project_settings

from data_analysis.config import API_KEY, SECRET_KEY

df_words_usa = None
df_words_eur = None

def get_df_words(access_token, data, keywords, pos, flag):
    headers = {
        'content-type': 'application/json'
    }
    url_lexer = f'https://aip.baidubce.com/rpc/2.0/nlp/v1/lexer?charset=UTF-8&access_token={access_token}'
    for i in data:
        try:
            response = requests.post(url=url_lexer, headers=headers, json={'text': i['news']})
            if response:
                result = response.json()
                # 数据提取
                df_word = pd.DataFrame(result['items'])[['item', 'pos', 'ne']]
                # 提取目标词性
                df_word = df_word[df_word['pos'] == pos]
                # 添加列，设定为关键词
                df_word['keywords'] = keywords
                print('获取数据 >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>')
                if flag == 'usa':
                    global df_words_usa
                    df_words_usa = pd.concat([df_words_usa, df_word])

                elif flag == 'eur':
                    global df_words_eur
                    df_words_eur = pd.concat([df_words_eur, df_word])
            else:
                print(response.json())
        except:
            continue
        # 百度免费的QPS为2, 所以作延迟处理
        time.sleep(0.5)

class WeiboGraph(object):

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


    def words_counts(self, dfi, topn):
        return dfi['item'].value_counts().head(topn)


    def words_sum(self, words):
        return words.groupby(by=words.index).sum()

    def symbol_szie(self, count):
        if count < 100:
            ratio =  2
        elif count < 1000:
            ratio = 0.2
        else:
            ratio = 2 * math.pow(10, -len(str(count) + 3))
        return ratio

    def write_graph(self, words_sum, categories, nodes, links, title, render_name):
        ratio = self.symbol_szie(words_sum.max())
        for i in range(len(words_sum)):
            nodes.append({
                'name': words_sum.index[i],
                'value': str(words_sum.values[i]),
                'symbolSize': str(words_sum.values[i] * ratio),
                'category': 1
            })
        c = (
            Graph(init_opts=opts.InitOpts(
                    width='1200px',
                    height='900px',
                    page_title=title))
                .add(
                    "",  # 系列名称
                    nodes,  # 关系图节点数据项列表
                    links,  # 关系图节点间关系数据项列表
                    categories,  # 关系图节点分类的类目列表
                    is_roam=False,  # 是否开启鼠标缩放和平移漫游
                    is_rotate_label=False,  # 是否旋转标签，默认不旋转
                    layout='circular',  # 图的布局, 'circular' 采用环形布局, 'force' 采用力引导布局
                    label_opts=opts.series_options.LabelOpts(
                        is_show=True,
                    ),  # 标签配置项
                    linestyle_opts=opts.series_options.LineStyleOpts(
                        curve=0.1
                )
            )
                .set_global_opts(title_opts=opts.TitleOpts(title=title))
                .render(render_name)
        )



if __name__ == '__main__':
    # 创建队列
    wg = WeiboGraph()
    wg.get_token()
    data_usa, count_usa = wg.parse_data(collection='weibo:usa')
    data_eur, count_eur = wg.parse_data(collection='weibo:eur')
    t_usa = threading.Thread(target=get_df_words, args=(wg.access_token, data_usa, '美国', 'n', 'usa'))
    t_eur= threading.Thread(target=get_df_words, args=(wg.access_token, data_eur, '欧洲', 'n', 'eur'))
    t_usa.start()
    t_eur.start()
    record = [t_usa, t_eur]
    for t in record:
        t.join()

    words_c_usa = wg.words_counts(df_words_usa, 10)
    words_c_eur = wg.words_counts(df_words_eur, 10)

    links_usa = []
    for i in range(len(words_c_usa)):
        links_usa.append({'source': '美国', "target": words_c_usa.index[i]})

    links_eur = []
    for i in range(len(words_c_eur)):
        links_eur.append({'source': '欧洲', "target": words_c_eur.index[i]})

    words = pd.concat([words_c_usa, words_c_eur])

    words_sum = wg.words_sum(words)

    ratio = wg.symbol_szie(max(count_usa, count_eur))

    categories = [{'name': '地区'}, {'name': '新闻关键词'}]

    nodes_base = [
        {
            'name': '美国',
            'value': str(count_usa),
            'symbolSize': str(ratio * count_usa),
            'category': 0
        },
        {
            'name': '欧洲',
            'value': str(count_eur),
            'symbolSize': str(ratio * count_eur),
            'category': 0
        }
    ]

    links = links_eur + links_usa
    wg.write_graph(words_sum, categories, nodes_base, links, title='美欧实时新闻关系', render_name='render_graph.html')