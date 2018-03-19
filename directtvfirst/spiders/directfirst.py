from scrapy import Request
import scrapy
from scrapy.log import WARNING
import json
import csv
import os
import traceback

zip_codes = []
dma_names = []
Channels = []
Genere = []

try:
    with open(os.path.abspath('DirecTV_input.csv'), 'r') as f:
        reader = csv.reader(f)
        for row in reader:
            zip_codes.append(row[2])
            dma_names.append(row[0])

except Exception as e:
    print('parse_csv Function => Got Error: {}'.format(e))

try:
    with open(os.path.abspath('Channels.csv'), 'r') as f:
        reader = csv.reader(f)
        for row in reader:
            Channels.append(row[0])
            Genere.append(row[1])

except Exception as e:
    print('parse_csv Function => Got Error: {}'.format(e))


class SiteProductItem(scrapy.Item):
    Provider_Name = scrapy.Field()
    Package_Name = scrapy.Field()
    DMA_Name = scrapy.Field()
    Channel_Name = scrapy.Field()
    Channel_Genre = scrapy.Field()


class ATTProductsSpider (scrapy.Spider):
    name = "att_products"
    allowed_domains = ['att.com']

    start_urls = [
        'https://www.att.com/channellineup/tv/tvchannellineup.html?tvType=directv&cta_button=AddToCart&pricing_terms'
        '=true&lang=en']

    PROD_URL = "https://www.att.com/apis/channellineup/getChannelData?_=1521230061137"

    def start_requests(self):
        for index, zipCode in enumerate(zip_codes[1:]):
            yield Request(
                url=self.PROD_URL,
                callback=self.parse_product,
                method="POST",
                body=json.dumps({"county": "SINGLE_COUNTY", "isLatino": "false", "tvType": "dtv", "zipCode": zipCode}),
                dont_filter=True,
                meta={'zip_code': zipCode, 'dma_name': dma_names[index + 1]},
                headers={
                    "content-type": "application/json",
                    "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) "
                                  "Chrome/64.0.3282.186 Safari/537.36",

                }
            )

    def parse_product(self, response):
        final_channels = []
        product = SiteProductItem()
        dma_name = response.meta['dma_name']
        channel_data = []
        package_data = []
        channel_list = []
        package_list = []
        try:
            data = json.loads(response.body).get('channelLineupDetails')
            channel_data = data.get('channelGroups')
            package_data = data.get('packages')
        except:
            self.log(
                "Failed parsing json at {} - {}".format(response.url, traceback.format_exc())
                , WARNING)

        for channel in channel_data:
            channel_list.append(channel.get('sortName'))

        for package in package_data:
            package_list.append(package.get('packageName'))

        for channel in channel_list:
            for i, c in enumerate(Channels):
                if channel.lower() == c.lower():
                    final_channels.append(c)

        for package in package_list:
            for channel in final_channels:
                for i, c in enumerate(Channels):
                    if channel.lower() == c.lower():
                        product['Provider_Name'] = "AT&T DirecTV"
                        product['Package_Name'] = package
                        product['Channel_Name'] = c
                        product['Channel_Genre'] = Genere[i]
                        product['DMA_Name'] = dma_name

                        yield product