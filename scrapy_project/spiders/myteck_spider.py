import scrapy
from scrapy_playwright.page import PageMethod
from ..items import MytekItem


class MytekSpider(scrapy.Spider):
    name = "myteck_spider"

    start_urls = [
        "https://www.mytek.tn/informatique/ordinateurs-portables/pc-portable.html",
    ]

    custom_settings = {
        "DOWNLOAD_HANDLERS": {
            "http": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
            "https": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
        },
        "TWISTED_REACTOR": "twisted.internet.asyncioreactor.AsyncioSelectorReactor",
        "PLAYWRIGHT_BROWSER_TYPE": "chromium",
        "PLAYWRIGHT_DEFAULT_NAVIGATION_TIMEOUT": 30000,
        "PLAYWRIGHT_LAUNCH_OPTIONS": {"headless": True},
    }

    def start_requests(self):
        for url in self.start_urls:
            yield scrapy.Request(
                url,
                meta={
                    "playwright": True,
                    "playwright_page_methods": [
                        PageMethod("wait_for_selector", "div.product-container"),
                    ],
                },
                callback=self.parse,
            )

    async def parse(self, response):
        products = response.css("div.product-container")

        for p in products:
            yield {
                "title": p.css("a.product-item-link::text").get(default="").strip(),
                "price": p.css("span.final-price::text").get(),
                "image": p.css(".product-item-photo img::attr(src)").get(),
                "url": p.css("a.product-item-link::attr(href)").get(),
                "availability": p.css("div.stock.availables span::text").get(default="Unknown"),
                "short_description": p.css("div.search-short-description::text").get(),
                "category": response.url.split("/")[4],
            }

        next_page = response.css('li.page-item a.page-link[aria-label="Next"]::attr(href)').get()

        if next_page:
            next_page = response.urljoin(next_page)
            yield scrapy.Request(
                next_page,
                meta={
                    "playwright": True,
                    "playwright_page_methods": [
                        PageMethod("wait_for_selector", "div.product-container"),
                    ],
                },
                callback=self.parse,
            )

