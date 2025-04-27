import scrapy
import time
from selenium import webdriver

class AlkotekaSpider(scrapy.Spider):

    name = "spider_name"
    allowed_domains = ["alkoteka.com"]

    def __init__(self, *args, **kwargs):
        super(AlkotekaSpider, self).__init__(*args, **kwargs)
        self.driver = webdriver.Chrome()
        try:
            with open('start_urls.txt', 'r') as f:
                self.start_urls = [url.strip() for url in f.readlines()]
        except FileNotFoundError:
            self.logger.error("Файл start_urls.txt не найден. Используются значения по умолчанию.")
            self.start_urls = ["https://alkoteka.com/catalog/vino", "https://alkoteka.com/catalog/krepkiy-alkogol", "https://alkoteka.com/catalog/slaboalkogolnye-napitki-2"]

    def parse(self, response):

        last_height = self.driver.execute_script("return document.body.scrollHeight")
        while True:
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
            new_height = self.driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                break
            last_height = new_height

        product_links = response.xpath('//div[@class="card-product"]//a/@href').getall()
        if product_links:
            for link in product_links:
                yield scrapy.Request(link, callback=self.parse_product, cookies={'region': 'Краснодар'})

    def parse_product(self, response):
        item = {
            "timestamp": int(time.time()),
            "RPC": response.xpath('//div[@class="product-card__header"]/p/text()').get(),
            "url": response.url,
            "title": self.parse_title(response),
            "marketing_tags": self.parse_marketing_tags(response),
            "brand": self.parse_brand(response),
            "section": response.xpath('//div[@class="breadcrumbs"]//a[@class="button button--simplified button--link"]//p/text()').getall(),
            "price_data": self.parse_price(response),
            "stock": self.parse_stock(response),
            "assets": self.parse_assets(response),
            "metadata": self.parse_metadata(response),
            "variants": 1,
        }
        yield item

    def parse_title(self, response):
        name = response.xpath('//div[@class="product-card"]//h1/text()').get(default='').strip()
        volume = response.xpath('//*[@id="root"]/main/section/div[2]/div[2]/div/div[2]/button[1]/p/text()').get(default='').strip()
        return f"{name}, {volume}" if volume else name

    def parse_marketing_tags(self, response):
        tags = []
        marketing_tags = response.xpath('//div[@class="product-card__tags"]//p/text()').getall()
        for tag in marketing_tags:
            if tag == 'Скидка' or tag == '-10% онлайн':
                tags.append(tag)
                break
        return tags

    def parse_brand(self, response):
        chars = response.xpath('//div[@class="specifications-card"]')
        brands = ''
        for char in chars:
            brand_span = char.xpath('./span[text()="Бренд"]/text()').get()
            if brand_span == "Бренд":
                brands = char.xpath('.//p[@class="text--body"]/text()').get()
        return brands

    def parse_price(self, response):
        original_price = response.xpath('//*[@id="root"]/main/section/div[2]/div[2]/div/div[4]/div/div[2]/div/p/text()').get().replace('&nbsp;', '').replace(' ', '').replace('₽', '').strip()
        current_price = response.xpath('//*[@id="root"]/main/section/div[2]/div[2]/div/div[4]/div/div[2]/p/text()').get().replace('&nbsp;', '').replace(' ', '').replace('₽', '').strip()
        sale_tag = ""
        if current_price and original_price:
            current_price = float(current_price)
            original_price = float(original_price)
            if original_price > current_price:
                discount_percentage = round((original_price - current_price) / original_price * 100)
                sale_tag = f"Скидка {discount_percentage}%"
        else:
            current_price = original_price = float(original_price)
        return {
            "current": current_price,
            "original": original_price,
            "sale_tag": sale_tag
        }

    def parse_stock(self, response):
        in_stock = True # На сайте отображаются только те товары, которые есть в наличии
        count = 0
        return {
            "in_stock": in_stock,
            "count": int(count),
        }

    def parse_assets(self, response):
        main_image = response.xpath('//div[@class="product-info__hero-img-wrap"]//img/@src').get()
        return {
            "main_image": main_image,
            "set_images": [],
            "view360": [],
            "video": []
        }

    def parse_metadata(self, response):
        descriptions = response.xpath('//div[@class="product-info__item"]')
        description = ''
        for desc in descriptions:
            brand_span = desc.xpath('./h3[text()="Описание"]/text()').get()
            if brand_span == "Описание":
                description = desc.xpath('.//p//text()').get().replace(' ', ' ')
        metadata = {
            "__description": description
        }
        keys = response.xpath('//div[@class="specifications-card"]//span/text()').getall()
        values = response.xpath('//div[@class="specifications-card"]//p[@class="text--body"]/text()').getall()
        for key, value in zip(keys, values):
            metadata[key] = value
        return metadata