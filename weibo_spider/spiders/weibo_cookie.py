# -*- coding: utf-8 -*-
import scrapy
from datetime import datetime, timedelta
from urllib import parse
import re

from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from weibo_spider.utils import card_act_int
from weibo_spider.items import WeiboSpiderItem

class WeiboCookieSpider(CrawlSpider):
    name = 'weibo_cookie'
    allowed_domains = ['weibo.com', 'sina.com.cn']
    page_links = LinkExtractor(restrict_xpaths='//div[@class="m-page"]//ul[@class="s-scroll"]/li/a')
    rules = (
        Rule(page_links, callback='parse_subjects', follow=True),
    )
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


    def __int__(self, subject=None, *args, **kwargs):
        super(WeiboCookieSpider, self).__init__(*args, **kwargs)
        self.subject = subject

    # 动态修改起始url
    def start_requests(self):
        self.start_urls = [f'https://s.weibo.com/weibo/{parse.quote(self.subject)}?topnav=1&wvr=6', ]
        for url in self.start_urls:
            yield scrapy.Request(url, callback=self.parse)



    def parse_subjects(self, response):
        div_list = response.xpath('//div[@class="m-con-l"]/div/div[@class="card-wrap"]')
        for odiv in div_list:
            item = WeiboSpiderItem()
            item['title'] = odiv.xpath('./div[@class="card-top"]//a/text()').extract_first()
            if item['title']:
                item['title'] = item['title'].strip()
            item['avatar'] = odiv.xpath('./div[@class="card"]//div[@class="avator"]/a/img/@src').extract_first()
            item['nickname'] = odiv.xpath('./div[@class="card"]//div[@class="content"]/div[@class="info"]/div[2]/a[1]/text()').extract_first()
            item['icon'] = odiv.xpath('./div[@class="card"]//div[@class="content"]/div[@class="info"]/div[2]/a[2]/@title').extract_first()
            news = odiv.xpath('./div[@class="card"]//div[@class="content"]/p[@class="txt"]')
            if len(news) == 1:
                item['news'] = news[0].xpath('string(.)').extract_first().replace('\n', '').replace(' ', '').replace('\u200b', '').replace('收起全文d', '')
            else:
                item['news'] = news[1].xpath('string(.)').extract_first().replace('\n', '').replace(' ', '').replace('\u200b', '').replace('收起全文d', '')
            time = odiv.xpath('./div[@class="card"]//div[@class="content"]/p[@class="from"]/a[1]/text()').extract_first()
            now = datetime.now()
            if '秒' in time:
                time = datetime.strftime(now - timedelta(seconds=int(time.split('秒')[0])), '%Y-%m-%d %H:%M:%S')
            elif '分钟' in time:
                time = datetime.strftime(now- timedelta(minutes=int(time.split('分钟')[0])), '%Y-%m-%d %H:%M:%S')
            elif '今天' in time:
                today = re.findall(r'\d+', time)
                time = str(datetime(now.year, now.month, now.day, hour=int(today[0]), minute=int(today[1]), second=0))
            else:
                date = re.findall(r'\d+', time)
                time = str(datetime(now.year, month=int(date[0]), day=int(date[1]), hour=int(date[2]), minute=int(date[3]), second=0))
            item['time'] = time
            item['origin'] = odiv.xpath('./div[@class="card"]//div[@class="content"]/p[@class="from"]/a[2]/text()').extract_first()
            item['collect'] = card_act_int(odiv.xpath('./div[@class="card"]/div[@class="card-act"]/ul/li[1]/a/text()').extract_first().strip().split(' '))
            item['forward'] = card_act_int(odiv.xpath('./div[@class="card"]/div[@class="card-act"]/ul/li[2]/a/text()').extract_first().strip().split(' '))
            item['comment'] = card_act_int(odiv.xpath('./div[@class="card"]/div[@class="card-act"]/ul/li[3]/a/text()').extract_first().strip().split(' '))
            item['like'] = card_act_int(odiv.xpath('./div[@class="card"]/div[@class="card-act"]/ul/li[4]/a/em/text()').extract_first())
            yield item




