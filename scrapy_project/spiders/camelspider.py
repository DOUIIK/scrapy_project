import scrapy
from scrapy_playwright.page import PageMethod


class CamelTestSpider(scrapy.Spider):
    name = "camelspider"

    start_urls = [
        "https://camelcamelcamel.com/popular"
    ]

    def start_requests(self):
        for url in self.start_urls:
            yield scrapy.Request(
                url,
                meta={
                    "playwright": True,
                    "playwright_page_methods": [
                        PageMethod("wait_for_timeout", 5000),
                    ],
                },
                callback=self.parse,
            )

    def parse(self, response):

        title = response.css("a::text").getall()
        page_text_sample = response.text[:300]

        yield {
            "url": response.url,
            "title": title,
            "text_sample": page_text_sample,
        }
