# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


#def serialize_price (value) :
#    return f' € {str(value)}'


class DiscountItem(scrapy.Item):
    """Item for storing discount product information from FromAustria"""
    url = scrapy.Field()
    brand = scrapy.Field()
    name = scrapy.Field()
    original_price = scrapy.Field()
    sale_price = scrapy.Field()
    discount_percentage = scrapy.Field()
    price_per_unit = scrapy.Field()
    stock_info = scrapy.Field()
    category = scrapy.Field()
    timestamp = scrapy.Field()
