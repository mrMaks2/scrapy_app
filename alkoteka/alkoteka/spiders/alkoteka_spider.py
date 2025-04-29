import json
import scrapy
import time

class AlkotekaSpider(scrapy.Spider):

    name = "spider_name"
    prod_url = 'https://alkoteka.com/product/'
    api_url = 'https://alkoteka.com/web-api/v1/product'
    city_uuid = '?city_uuid=4a70f9e0-46ae-11e7-83ff-00155d026416' # uuid города Краснодар
    category_conf = '&root_category_slug='

    def __init__(self, *args, **kwargs):
        super(AlkotekaSpider, self).__init__(*args, **kwargs)
        try:
            with open('start_urls.txt', 'r') as f:
                self.start_urls = [
                    self.api_url + self.city_uuid + '&page=1' + self.category_conf + url.strip("https://alkoteka.com/catalog/")
                    for url in f.readlines()
                ]
        except FileNotFoundError:
            self.logger.error("Файл start_urls.txt не найден. Используются значения по умолчанию.")
            self.start_urls = [
                self.api_url + self.city_uuid + '&page=1' + self.category_conf + "vino",
                self.api_url + self.city_uuid + '&page=1' + self.category_conf + "krepkiy-alkogol",
                self.api_url + self.city_uuid + '&page=1' + self.category_conf + "slaboalkogolnye-napitki-2"
            ]

    def start_requests(self):
        for url in self.start_urls:
            yield scrapy.Request(url=url, callback=self.parse)

    def parse(self, response):
        try:
            product_links = response.json()
            if product_links:
                for link in product_links['results']:
                    category_slug = link['slug']
                    url = self.api_url + '/' + category_slug + self.city_uuid
                    yield scrapy.Request(url=url, callback=self.parse_product)
            while product_links['meta']['has_more_pages']:
                page = product_links['meta']['current_page']
                url = response.url.replace('&page=' + str(page), '&page=' + str(page + 1))
                yield scrapy.Request(url=url, callback=self.parse)

        except json.JSONDecodeError:
            self.logger.error("Не удалось декодировать JSON из ответа API.")
        except Exception as e:
            self.logger.error(f"Произошла ошибка при обработке ответа API: {e}")

    def parse_product(self, response):

        products = response.json()['results']
        original_price = float(products['price_details'][0]['prev_price'])
        current_price = float(products['price_details'][0]['price'] if products['price_details'][0]['price'] else products['price_details'][0]['prev_price'])
        keys = [prod['title'] for prod in products['description_blocks']]

        values = []
        for prod in products['description_blocks']:
            if prod['code'] != 'obem' and prod['code'] != 'krepost' and prod['code'] != 'podarocnaya-upakovka':
                values.append(prod['values'][0]['name'])
            elif prod['min']:
                values.append(prod['min'])
            else:
                values.append('Неизместные данные')

        brand = ''
        for prod in products['description_blocks']:
            if prod['code'] == "brend":
                brand = prod['values'][0]['name']

        description = ''
        for desc in products['text_blocks']:
            if desc['title'] == 'Описание':
                description = desc['content']


        item = {
            "timestamp": int(time.time()),
            "RPC": products['vendor_code'],
            "url": response.url,
            "title": products['name'] + [prod['title'] for prod in products['filter_labels'] if prod['filter'] == "obem"][0],
            "marketing_tags": [prod['title'] for prod in products['filter_labels'] if prod['filter'] == "dopolnitelno" or prod['filter'] == "tovary-so-skidkoi"],
            "brand": brand,
            "section": [products['category']['name']],
            "price_data": {
                "original": original_price,
                "current": current_price,
                "sale_tag": f'Скидка {round((original_price - current_price) / original_price * 100)}%' if original_price and current_price else ''
            },
            "stock": {
                "in_stock": products['available'],
                "count": int(products['quantity_total']),
            },
            "assets": {
                "main_image": products['image_url'],
                "set_images": [],
                "view360": [],
                "video": []
            },
            "metadata": {
                "__description": description
            },
            "variants": 1,
        }

        for key, value in zip(keys, values):
            item['metadata'][key] = value

        yield item
