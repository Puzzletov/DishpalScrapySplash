import scrapy
from scrapy_playwright.page import PageMethod

class ZalandoDataSpider(scrapy.Spider):
    name = "zolando_debug"
    start_urls =     [
        "https://www.zalando.co.uk/childrens-sale/",
        "https://www.zalando.co.uk/mens-sale/",
        "https://www.zalando.co.uk/womens-sale/"
    ]

    
    custom_settings = {
        "DEFAULT_REQUEST_HEADERS": {
            "User-Agent": (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_0) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/123.0.0.0 Safari/537.36"
            ),
            "Accept-Language": "en-US,en;q=0.9",
        },
        "ROBOTSTXT_OBEY": False,
    }
    
    def start_requests(self):
        for url in self.start_urls:
            yield scrapy.Request(
                url=url,
                callback=self.parse,
                errback=self.errback_handler,
                meta={
                    "playwright": True,
                    "playwright_include_page": True,
                    "playwright_page_goto_kwargs": {
                        "timeout": 120000,         # Allow up to 120 seconds for the page to load
                        "wait_until": "domcontentloaded"  # Wait for the initial DOM to be ready
                    },
                    "playwright_page_methods": [
                        PageMethod("wait_for_load_state", "domcontentloaded"),
                        PageMethod("evaluate", "window.scrollTo(0, document.body.scrollHeight)"),
                        PageMethod("wait_for_timeout", 10000),  # Extra wait to allow lazy-loaded content to finish rendering
                    ],
                },
                headers={
                    "User-Agent": (
                        "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_0) "
                        "AppleWebKit/537.36 (KHTML, like Gecko) "
                        "Chrome/123.0.0.0 Safari/537.36"
                    ),
                    "Accept-Language": "en-US,en;q=0.9",
                },
            )

    def parse(self, response):
        # self.logger.info("Processing URL: %s", response.url)
        
        # # Optional: Save the fully rendered HTML to a file (useful for debugging the structure)
        # with open("debug_page.html", "w", encoding="utf-8") as f:
        #     f.write(response.text)
        # self.logger.info("Rendered HTML saved to debug_page.html!")
        
        # def to_float(price_str):
        #     if price_str:
        #         try:
        #             return float(price_str.replace("€", "")
        #                                      .replace("\xa0", "")
        #                                      .replace(",", ".")
        #                                      .strip())
        #         except ValueError:
        #             self.logger.warning("Could not convert price: %s", price_str)
        #     return None
        
        parent = response.css("div.L5YdXz._0xLoFW._7ckuOK.mROyo1")
        cards = parent.css("div._5qdMrS._75qWlu.iOzucJ")
        # self.logger.info("Found %s product card(s)", len(cards))
        
        for card in cards:
            discount_percent_text = card.css("ul._28osyf span::text").get()
            discount_percent = discount_percent_text.strip() if discount_percent_text else None

            product_link = card.xpath(".//a[contains(@class, 'CKDt_l') and @tabindex='-1']/@href").get()
            if not product_link:
                product_link = card.css("a.CKDt_l::attr(href)").get()

            brand = card.css("header div.Zhr-fS h3.OBkCPz::text").get()
            name = card.css("header div.Zhr-fS h3.voFjEy::text").get()

            price_spans = card.css("header section._0xLoFW._78xIQ- p span.voFjEy::text").getall()

            new_price_raw = price_spans[0].strip() if len(price_spans) > 0 else None
            old_price_raw = price_spans[1].strip() if len(price_spans) > 1 else None

            def price_to_float(price_str):
                if price_str:
                    try:
                        return float(price_str.replace("£", "").strip())
                    except ValueError:
                        self.logger.warning("Unable to convert price: %s", price_str)
                return None

            new_price = price_to_float(new_price_raw)
            old_price = price_to_float(old_price_raw)

            # --- Calculate Discount Amount ---
            discount_value = None
            if old_price is not None and new_price is not None:
                discount_value = round(old_price - new_price, 2)

            yield {
                "brand": brand,
                "name": name,
                "product_link": product_link,
                "new_price": new_price,
                "old_price": old_price,
                "discount": discount_value,
                "discount_percent": discount_percent
            }

    def errback_handler(self, failure):
        self.logger.error("Request failed: %s", repr(failure))
        
        # Check if the failure is a timeout error or similar exception
        if failure.check(Exception):
            self.logger.info("Timeout or other error occurred; retrying the request for %s", failure.request.url)
            yield scrapy.Request(
                url=failure.request.url,
                callback=self.parse,
                errback=self.errback_handler,
                meta=failure.request.meta,  # Reuse the meta settings from the failed request
                headers=failure.request.headers,
                dont_filter=True
            )
