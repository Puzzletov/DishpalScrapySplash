import scrapy
from scrapy_splash import SplashRequest
from discountscraper.items import DiscountItem
import logging

class DiscountSpider(scrapy.Spider):
    name = 'discountspider'
    allowed_domains = ['fromaustria.com']
    start_urls = ['https://www.fromaustria.com/de-AT/angebote']  # Changed to direct discount page
    
    lua_script = """
    function main(splash, args)
        -- Configure viewport and timeout
        splash:set_viewport_size(1920, 1080)
        splash.private_mode_enabled = false
        splash:set_user_agent('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        
        -- Go to URL and wait for initial load
        assert(splash:go(args.url))
        assert(splash:wait(3))
        
        -- Handle cookie consent
        local consent_button = splash:select('button[data-testid="uc-accept-all-button"]')
        if consent_button then
            consent_button:mouse_click()
            splash:wait(2)
        end
        
        -- Scroll simulation for dynamic loading
        for i = 1, 6 do
            splash:evaljs("window.scrollTo(0, document.body.scrollHeight * " .. i .. "/6)")
            splash:wait(1)
        end
        
        -- Final wait for all content to load
        splash:wait(2)
        
        -- Get next page button status
        local next_button = splash:select('button.pagination__btn--next')
        local has_next = next_button ~= nil and not next_button:hasClass('disabled')
        
        -- Click next if requested
        if args.click_next and has_next then
            next_button:mouse_click()
            splash:wait(3)
            
            -- Scroll new page
            for i = 1, 6 do
                splash:evaljs("window.scrollTo(0, document.body.scrollHeight * " .. i .. "/6)")
                splash:wait(1)
            end
        end
        
        return {
            html = splash:html(),
            has_next = has_next,
            cookies = splash:get_cookies(),
            url = splash:url()
        }
    end
    """
    
    def start_requests(self):
        for url in self.start_urls:
            yield SplashRequest(
                url=url,
                callback=self.parse,
                endpoint='execute',
                args={
                    'lua_source': self.lua_script,
                    'wait': 3,
                    'timeout': 90,
                    'click_next': False
                },
                dont_filter=True,
                meta={'page': 1}
            )
    
    def parse(self, response):
        try:
            # Log current page
            current_page = response.meta.get('page', 1)
            self.logger.info(f"Parsing page {current_page}: {response.url}")
            
            # Parse product list
            products = response.css('ul#productList > li.productCard')
            self.logger.info(f"Found {len(products)} products on page {current_page}")
            
            for product in products:
                item = DiscountItem()
                
                # Extract product information
                item['brand'] = product.css('.productCard__title strong.productCard__brand::text').get()
                item['name'] = product.css('.productCard__title a.productCard__link::text').get()
                item['sale_price'] = product.css('.productCard__price .price--reduced::text').get()
                item['original_price'] = product.css('.productCard__price .instead-price::text').get()
                item['price_per_unit'] = product.css('.productCard__price .price--perUnit::text').get()
                item['discount_percentage'] = product.css('.productCard__tags .flag.sale-tag.small.percent::text').get()
                item['stock_info'] = product.css('.productCard__stock::text').get()
                item['url'] = response.urljoin(product.css('.productCard__title a.productCard__link::attr(href)').get())
                
                # Only yield items with both prices
                if item['sale_price'] and item['original_price']:
                    yield item
            
            # Handle pagination
            has_next = response.data.get('has_next', False)
            if has_next and current_page < 10:  # Limit to 10 pages for testing
                self.logger.info(f"Following next page {current_page + 1}")
                yield SplashRequest(
                    url=response.url,
                    callback=self.parse,
                    endpoint='execute',
                    args={
                        'lua_source': self.lua_script,
                        'wait': 3,
                        'timeout': 90,
                        'click_next': True,
                        'cookies': response.data.get('cookies', [])
                    },
                    dont_filter=True,
                    meta={'page': current_page + 1}
                )
            
        except Exception as e:
            self.logger.error(f"Error parsing page {response.url}: {str(e)}")