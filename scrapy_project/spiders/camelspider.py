import scrapy
from scrapy_playwright.page import PageMethod


class MytekModernSpider(scrapy.Spider):
    name = "myteck_modern"

    # Put the category URLs you want to scrape here
    start_urls = [
        "https://www.mytek.tn/informatique/ordinateur-de-bureau/ecran.html",
        "https://www.mytek.tn/informatique/peripheriques-accessoires/clavier-souris.html",
    ]

    # Keep Playwright config local to this spider to avoid interfering with other spiders
    custom_settings = {
        "DOWNLOAD_HANDLERS": {
            "http": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
            "https": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
        },
        "TWISTED_REACTOR": "twisted.internet.asyncioreactor.AsyncioSelectorReactor",
        "PLAYWRIGHT_BROWSER_TYPE": "chromium",
        # Playwright launch options
        "PLAYWRIGHT_LAUNCH_OPTIONS": {"headless": True},
        # Navigation timeout in ms (adjust if site is slow)
        "PLAYWRIGHT_DEFAULT_NAVIGATION_TIMEOUT": 30000,
        # Optional: lower concurrency if you hit resource limits
        # "CONCURRENT_REQUESTS": 4,
    }

    def start_requests(self):
        """Start requests with Playwright enabled and wait until product blocks load."""
        for url in self.start_urls:
            yield scrapy.Request(
                url,
                meta={
                    "playwright": True,
                    # Run PageMethod(s) before Scrapy receives the response
                    "playwright_page_methods": [
                        # wait until at least one product item is present
                        PageMethod("wait_for_selector", "div.product-item-info"),
                        # optional: wait a short additional time for dynamic assets (ms)
                        # PageMethod("wait_for_timeout", 500),
                        # optional: ensure lazy images have loaded by scrolling
                        PageMethod("evaluate", "window.scrollTo(0, document.body.scrollHeight)"),
                        PageMethod("wait_for_timeout", 300),
                    ],
                    # Use "playwright_page_methods" only if your package supports it (0.0.44+)
                },
                callback=self.parse,
            )

    async def parse(self, response):
        """
        Parse listing pages (products grid) and follow pagination.
        This runs after the page methods above are executed.
        """
        products = response.css("div.product-item-info")

        for p in products:
            title = p.css("a.product-item-link::text").get(default="").strip()
            price = p.css("span.price::text").get()
            image = p.css("img.product-image-photo::attr(src)").get()
            url = p.css("a.product-item-link::attr(href)").get()
            availability = p.css("div.stock.available span::text").get(default="Unknown")

            # Yield a simple item; pipelines can process/clean/save this
            yield {
                "title": title,
                "price": price,
                "image": response.urljoin(image) if image else None,
                "url": response.urljoin(url) if url else None,
                "availability": availability,
                "source_page": response.url,
            }

        # Pagination: follow the "next" button if present (Magento typical selector)
        next_page = response.css("a.action.next::attr(href)").get()
        if next_page:
            yield scrapy.Request(
                response.urljoin(next_page),
                meta={
                    "playwright": True,
                    "playwright_page_methods": [
                        PageMethod("wait_for_selector", "div.product-item-info"),
                        PageMethod("evaluate", "window.scrollTo(0, document.body.scrollHeight)"),
                        PageMethod("wait_for_timeout", 300),
                    ],
                },
                callback=self.parse,
            )
