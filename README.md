# weibo_spider

分别采用Scrapy、crawlScrapy、redis-crawlScrapy模拟新浪微博登录并抓取热点，保存相应的数据并对结果进行分析



## 安装

```
pip3 install -r requirements.txt
```

## 基础配置 

### 接口基本配置(修改配置文件`weibo_spider/weibo_spider/settings.py` )

```python
# MySql相关配置(如果要将结果保存至mysql, 这个需要配置, 同时将相应的管道('weibo_spider.pipelines.MySqlPipeline': 301)打开)
MYSQL_CONFIG = {
   'host': 'localhost',
   'port': 3306,
   'user': 'root',
   'password': 'jiang',
   'database': 'spiderinfo',
   'charset': 'utf8'
}

# MongoDB相关配置(如果要将结果保存至MongoDB, 这个需要配置, 同时将相应的管道('weibo_spider.pipelines.MyMongoPipeline': 302)打开)
MONGO_CONFIG = {
   'host': 'localhost',
   'port': 27017
}


# 如果采用redis分布式爬虫, 需要配置下面这几项
REDIS_HOST = '127.0.0.1'
REDIS_PORT = 6379
# 使用scrapy-redis组件的去重队列
DUPEFILTER_CLASS = "scrapy_redis.dupefilter.RFPDupeFilter"
# 使用scrapy-redis组建自己调度器
SCHEDULER = "scrapy_redis.scheduler.Scheduler"
# 是否允许暂停
SCHEDULER_PERSIST = True


```

### 说明

```
1、 pipeline.py文件已经支持保存至文件、MySql、MongoDB三种方式, 如果采用分布式爬虫直接保存在redis数据库

2、 middlewares.py文件中自定义cookie池和代理池, 使用时只需要打开配置文件中相应的管道即可, 也可以直接在相应的爬虫文件中自定义配置，修改custom_settings的配置

3、 items.py是爬取对应数据相应的字段

4、 manage*.py则是相应的启动文件, 当然也可以直接在终端命令运行相对应的命令, manage.py是采用Scrapy自己模拟登陆抓取信息的启动方式, manage_cookie.py是采用CrawlScrapy和cookie抓取信息的启动方式, manage_redis.py是采用RedisCrawlScrapy分布式爬取的启动方式, 当然采用分布式爬取时需要打开主客户机的redis输入命令起始urlZ, 即lpush weibo_redis:start_urls "https://s.weibo.com/weibo/xxxxxx?topnav=1&wvr=6"

5、 graph_analysis.py是分析结果并用关系图展示

6、 cloud_analysis.py是分析结果并用词云图展示
```


## 自定义配置

在相对应的爬虫文件中可以添加自定义配置，例如在weibo_cookie.py中配置：
```python
# 自己定制配置文件
custom_settings = {
    'ITEM_PIPELINES': {
        'weibo_spider.pipelines.MyMongoPipeline': 302
    },
    'DOWNLOADER_MIDDLEWARES': {
        # 使用自定义的cookie池
        'weibo_spider.middlewares.CookiesMiddleware': 544,
        'weibo_spider.middlewares.ProxyMiddleware': 545
    },
    # 使用cookie池
    'COOKIES_URL': 'http://192.168.199.233:5000/weibo/random',
    # 使用代理池
    'PROXY_URL': 'http://localhost:5555/random'
}
```


## 使用cookie池服务(git@github.com:lajos182/CookiesPool.git)

## 使用代理池服务(git@github.com:lajos182/ProxyPool.git)

## 运行

```
若要采用scrapy模拟登陆爬取, 使用python manage.py
若要采用cookie/proxy+crawlscrapy, 使用python manage_cookie.py
若要采用cookie/proxy+rediscrawlscrapy, 使用python manage_redis.py
若要进行数据分析获取关系图graph, 使用python graph_analysis.py
若要进行数据分析获取词云图cloudword, 使用python cloud_analysis.py
```

## 运行效果

### 爬虫运行效果：
![爬虫运行](https://github.com/lajos182/weibo_spider/blob/master/run_image/%E7%88%AC%E8%99%AB%E8%BF%90%E8%A1%8C.png)

### mongo数据结果展示
![mongno数据展示](https://github.com/lajos182/weibo_spider/blob/master/run_image/mongo_lzx.png)

### 关系图展示
![关系图](https://github.com/lajos182/weibo_spider/blob/master/run_image/graph.png)

### 词云图展示
![词云图](https://github.com/lajos182/weibo_spider/blob/master/run_image/cloud.png)

