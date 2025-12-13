import scrapy
from scrapy_project.utils.flaresolverr import fetch_with_flaresolverr
from scrapy.http import HtmlResponse


class CamelFlareSolverrSpider(scrapy.Spider):
    name = "camel_flaresolverr_scraper"

    start_urls = [
        "https://camelcamelcamel.com/popular"
    ]

    def start_requests(self):
        for url in self.start_urls:
            yield scrapy.Request(
                url=url,
                callback=self.parse_with_flaresolverr,
                dont_filter=True,
                meta={
                    "handle_httpstatus_all": True
                }
            )

    def parse_with_flaresolverr(self, response):
        html = fetch_with_flaresolverr(response.url)

        fake_response = HtmlResponse(
            url=response.url,
            body=html,
            encoding="utf-8",
        )

        titles = fake_response.css("a::text").getall()
        titles = [t.strip() for t in titles if t and len(t.strip()) > 25]

        yield {
            "titles_count": len(titles),
            "sample_titles": titles[:5],
        }
