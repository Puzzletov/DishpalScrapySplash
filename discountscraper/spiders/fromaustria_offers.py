import scrapy
import re
import math
from scrapy_playwright.page import PageMethod

class FromAustriaSpider(scrapy.Spider):
    name = "fromaustria"
    # start_urls = [
    #     "https://www.zalando.co.uk/mens-sale",
    #     "https://www.zalando.co.uk/women-home", 
    #     "https://www.zalando.co.uk/kids-home"
    # ]
    start_urls = [
        "https://www.fromaustria.com/en/deals-1"
    ]
    
    custom_settings = {
        "DEFAULT_REQUEST_HEADERS": {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/122.0.0.0 Safari/537.36"
            )
        }
    }
    
    def start_requests(self):
        # Start with page 1
        for url in self.start_urls:
            yield scrapy.Request(
                url=url,
                callback=self.parse,
                meta={
                    "playwright": True,
                    "playwright_include_page": True,
                    # Increase the navigation timeout to 60 seconds
                    "playwright_page_goto_timeout": 60000,
                    "playwright_page_methods": [
                        # Wait until network activity is quiet
                        PageMethod("wait_for_load_state", "networkidle"),
                        # Scroll down to trigger lazy-loaded content
                        PageMethod("evaluate", "window.scrollTo(0, document.body.scrollHeight)"),
                        # Pause a bit to let lazy-loaded elements appear
                        PageMethod("wait_for_timeout", 2000),
                    ]
                }
            )
    
    def parse(self, response):
        self.logger.info("Processing URL: %s", response.url)
        
        # Save the rendered HTML for debugging purposes.
        with open("debug_page.html", "w", encoding="utf-8") as f:
            f.write(response.text)
        
        def to_float(price_str):
            if price_str:
                return float(
                    price_str.replace("€", "")
                             .replace("\xa0", "")
                             .replace(",", ".")
                             .strip()
                )
            return None
        
        # Extract products and calculate discount
        products = response.css("ul#productList > li")
        for product in products:
            brand = product.css(".productCard__brand::text").get()
            name = product.css(".productCard__link::text").get()
            new_price_raw = product.css(".price--reduced::text").get()
            old_price_raw = product.css(".instead-price::text").get()
            price_per_unit = product.css(".price--perUnit::text").get()
            product_link = product.css(".productCard__img__link::attr(href)").get()
            
            old_price = to_float(old_price_raw)
            new_price = to_float(new_price_raw)
            
            # Calculate discount percentage if possible.
            discount = None
            if old_price and new_price:
                discount = round(((old_price - new_price) / old_price) * 100, 2)
            
            yield {
                "brand": brand,
                "name": name,
                "old_price": old_price,
                "new_price": new_price,
                "price_per_unit": price_per_unit,
                "product_link": product_link,
                "discount": discount,
            }
        
        # Extract total items using the pagination footer text, e.g., "Deals: 31 - 60 of 321 items"
        pagination_text = response.css("p.productlist-footer__count::text").get()
        if pagination_text:
            self.logger.info("Pagination text: %s", pagination_text)
            match_total = re.search(r'of\s+(\d+)\s+items', pagination_text)
            match_range = re.search(r'(\d+)\s*-\s*(\d+)', pagination_text)
            if match_total and match_range:
                total_items = int(match_total.group(1))
                first_item = int(match_range.group(1))
                last_item = int(match_range.group(2))
                items_per_page = last_item - first_item + 1
                total_pages = math.ceil(total_items / items_per_page)
                self.logger.info("Total items: %d, Items per page: %d, Total pages: %d",
                                 total_items, items_per_page, total_pages)
                
                # Schedule pagination only on the first page to avoid duplicate requests.
                if "page=" not in response.url:
                    for page in range(2, total_pages + 1):
                        next_url = f"https://www.fromaustria.com/en/deals-1?page={page}"
                        self.logger.info("Scheduling next page: %s", next_url)
                        yield scrapy.Request(
                            url=next_url,
                            callback=self.parse,
                            meta={
                                "playwright": True,
                                "playwright_include_page": True,
                                "playwright_page_goto_timeout": 60000,
                                "playwright_page_methods": [
                                    PageMethod("wait_for_load_state", "networkidle"),
                                    PageMethod("evaluate", "window.scrollTo(0, document.body.scrollHeight)"),
                                    PageMethod("wait_for_timeout", 2000),
                                ]
                            }
                        )
            else:
                self.logger.warning("Could not match pagination pattern in text: %s", pagination_text)
        else:
            self.logger.info("No pagination count text found on this page.")
