# -*- coding: utf-8 -*-
import time
from datetime import datetime, timedelta
from urllib import parse
import re
import json

import scrapy
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from weibo_spider.utils import get_su, get_sp_rsa, card_act_int
from weibo_spider.items import WeiboSpiderItem

class WeiboSpider(CrawlSpider):
    name = 'weibo'
    allowed_domains = ['weibo.com', 'sina.com.cn']
    page_links = LinkExtractor(restrict_xpaths='//div[@class="m-page"]//ul[@class="s-scroll"]/li/a')
    rules = (
        Rule(page_links, callback='parse_subjects', follow=True),
    )

    # 自己定制配置文件
    custom_settings = {
        'ITEM_PIPELINES': {
            'weibo_spider.pipelines.MyMongoPipeline': 302,
        }
    }

    def __int__(self, login_name, login_password, subject=None, *args, **kwargs):
        super(WeiboSpider, self).__init__(*args, **kwargs)
        self.login_name = login_name
        self.login_password = login_password
        self.subject = subject


    def start_requests(self):
        # login_name = '18258720901'
        # login_password = 'jiang1593689***'
        su = get_su(self.login_name)
        data = {
            'entry': 'weibo',
            'callback': 'sinaSSOController.preloginCallBack',
            'su': su,
            'rsakt': 'mod',
            'checkpin': 1,
            'client': 'ssologin.js(v1.4.19)',
            '_': str(int(time.time()) * 1000)
        }
        query_string = parse.urlencode(data, safe='(,)')
        yield scrapy.Request(url=f'https://login.sina.com.cn/sso/prelogin.php?{query_string}', callback=self.parse_login, meta={'su': su, 'password': self.login_password})


    def parse_login(self, response):
        su = response.meta['su']
        password = response.meta['password']
        server_data = re.search(r'"servertime":(.*?),.*?"nonce":"(.*?)","pubkey":"(.*?)","rsakv":"(.*?)","is_openlock":(\d),.*?"smsurl":"(.*?)".*?', response.text, re.I)
        if server_data:
            servertime = server_data.group(1)
            nonce = server_data.group(2)
            pubkey = server_data.group(3)
            rsakv = server_data.group(4)
            is_openlock = server_data.group(5)
            # not_tab_qrcode = server_data.group(6)
            smsurl = server_data.group(6).replace('\\', '')
            sp = get_sp_rsa(password, weibo_rsa_n=pubkey, servertime=servertime, nonce=nonce)
            post_url = f'https://login.sina.com.cn/sso/login.php?client=ssologin.js(v1.4.19)'
            form_data = {
                'entry': 'weibo',
                'gateway': '1',
                'from': '',
                'savestate': '0',
                'qrcode_flag': 'false',
                'useticket': '1',
                'pagerefer': 'https://login.sina.com.cn/crossdomain2.php?action=logout&r=https%3A%2F%2Fpassport.weibo.com%2Fwbsso%2Flogout%3Fr%3Dhttps%253A%252F%252Fweibo.com%26returntype%3D1',
                # 'wsseretry': 'servertime_error',
                # 'pcid': 'gz-15b92fccfdbcffd9d892114c6c5219091385',
                # 'door': '111',  # 验证码
                'vsnf': '1',
                'su': su,
                'service': 'miniblog',
                'servertime': str(servertime),
                'nonce': nonce,
                'pwencode': 'rsa2',
                'rsakv': rsakv,
                'sp': sp,
                'sr': '1549*872',
                'encoding': 'UTF-8',
                # 'prelt': 186,
                'url': 'https://weibo.com/ajaxlogin.php?framelogin=1&callback=parent.sinaSSOController.feedBackUrlCallBack',
                'returntype': 'META',
            }
            yield scrapy.FormRequest(
                url=post_url,
                formdata=form_data,
                callback=self.parse_content
            )

    def parse_content(self, response):
        first_url = re.search(r'"retcode":(.*?),"arrURL":(.*?)}.*?', response.text, re.I)
        if first_url:
            retcode = first_url.group(1)
            home_list = eval(first_url.group(2).replace('\\', ''))
            yield scrapy.Request(url=home_list[0], callback=self.parse_home)

    def parse_home(self, response):
        data = re.search(r'{.*}', response.text, re.I)
        if data:
            data_dict = json.loads(data.group())
            # 登录成功
            if data_dict['result']:
                uniqueid = data_dict['userinfo']['uniqueid']
                displayname = data_dict['userinfo']['displayname']
                yield scrapy.Request(url=f'https://s.weibo.com/weibo/{parse.quote(self.subject)}?topnav=1&wvr=6')



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




