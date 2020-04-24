# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class WeiboSpiderItem(scrapy.Item):
    # define the fields for your item here like:
    title = scrapy.Field()
    avatar = scrapy.Field()
    nickname = scrapy.Field()
    icon = scrapy.Field()
    news = scrapy.Field()
    time = scrapy.Field()
    origin = scrapy.Field()
    collect = scrapy.Field()
    forward = scrapy.Field()
    comment = scrapy.Field()
    like = scrapy.Field()
