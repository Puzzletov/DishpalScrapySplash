# Define here the models for your spider middleware
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/spider-middleware.html

from scrapy import signals
from urllib.parse import urlencode
from random import randint
import requests
import logging
import os
import time
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# useful for handling different item types with a single interface
from itemadapter import is_item, ItemAdapter


###############################################################################
# 1) BOOKSCRAPER SPIDER MIDDLEWARE
###############################################################################
class DiscountscraperSpiderMiddleware:
    # Not all methods need to be defined. If a method is not defined,
    # Scrapy acts as if the spider middleware does not modify
    # the passed objects.

    @classmethod
    def from_crawler(cls, crawler):
        # This method is used by Scrapy to create your spiders.
        middleware = cls()
        crawler.signals.connect(middleware.spider_opened, signal=signals.spider_opened)
        return middleware

    def process_spider_input(self, response, spider):
        # Called for each response that goes through the spider
        # middleware and into the spider.
        #
        # Should return None or raise an exception.
        return None

    def process_spider_output(self, response, result, spider):
        # Called with the results returned from the Spider, after
        # it has processed the response.
        #
        # Must return an iterable of Request, or item objects.
        for i in result:
            yield i

    def process_spider_exception(self, response, exception, spider):
        # Called when a spider or process_spider_input() method
        # raises an exception.
        #
        # Should return either None or an iterable of Request/item objects.
        pass

    def process_start_requests(self, start_requests, spider):
        # Called with the start requests of the spider,
        # and works similarly to process_spider_output(),
        # except that it doesn't have a response associated.
        for r in start_requests:
            yield r

    def spider_opened(self, spider):
        spider.logger.info(f"Spider opened: {spider.name}")


###############################################################################
# 2) DISCOUNTSCRAPER DOWNLOADER MIDDLEWARE
###############################################################################
class DiscountscraperDownloaderMiddleware:
    # Not all methods need to be defined. If a method is not defined,
    # Scrapy acts as if the downloader middleware does not modify
    # the passed objects.

    @classmethod
    def from_crawler(cls, crawler):
        middleware = cls()
        crawler.signals.connect(middleware.spider_opened, signal=signals.spider_opened)
        return middleware

    def process_request(self, request, spider):
        # Called for each request going through the downloader middleware.
        return None

    def process_response(self, request, response, spider):
        # Called with the response returned from the downloader.
        return response

    def process_exception(self, request, exception, spider):
        # Called when a download handler or process_request() raises an exception.
        pass

    def spider_opened(self, spider):
        spider.logger.info(f"Spider opened: {spider.name}")


###############################################################################
# 3) SCRAPEOPS FAKE BROWSER HEADER MIDDLEWARE
###############################################################################
class ScrapeOpsFakeBrowserHeaderMiddleware:
    """Middleware to provide random browser headers for each request."""

    @classmethod
    def from_crawler(cls, crawler):
        return cls(crawler.settings)

    def __init__(self, settings):
        self.scrapeops_api_key = settings.get('SCRAPEOPS_API_KEY')
        self.scrapeops_endpoint = settings.get('SCRAPEOPS_BROWSER_HEADERS_ENDPOINT')
        self.scrapeops_enabled = settings.get('SCRAPEOPS_BROWSER_HEADERS_ENABLED', True)
        self.scrapeops_num_results = settings.get('SCRAPEOPS_NUM_RESULTS')
        self.browser_headers_list = []
        self._get_browser_headers_list()

    def _get_browser_headers_list(self):
        """Fetch a list of possible browser headers from ScrapeOps."""
        payload = {
            'api_key': self.scrapeops_api_key,
            'num_results': self.scrapeops_num_results
        }
        try:
            response = requests.get(url=self.scrapeops_endpoint, params=payload)
            json_response = response.json()
            self.browser_headers_list = json_response.get('result', [])
        except Exception as err:
            print(f'Error fetching browser headers: {err}')
            self.browser_headers_list = []

    def _get_random_browser_header(self):
        if not self.browser_headers_list:
            return None
        random_index = randint(0, len(self.browser_headers_list) - 1)
        return self.browser_headers_list[random_index]

    def process_request(self, request, spider):
        """Assign random headers to each request if enabled."""
        if self.scrapeops_enabled:
            random_browser_header = self._get_random_browser_header()
            if random_browser_header:
                header_mapping = {
                    'accept-language': 'en-US,en;q=0.9',
                    'sec-fetch-user': '?1',
                    'sec-fetch-mode': 'navigate',  # corrected from 'sec-fetch-mod'
                    'sec-fetch-site': 'none',
                    'sec-ch-ua-platform': '"Windows"',
                    'sec-ch-ua-mobile': '?0',
                    'sec-ch-ua': '"Google Chrome";v="120", "Chromium";v="120"',
                    'user-agent': ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                                   'AppleWebKit/537.36 (KHTML, like Gecko) '
                                   'Chrome/120.0.0.0 Safari/537.36'),
                    'upgrade-insecure-requests': '1',
                    'accept': (
                        'text/html,application/xhtml+xml,application/xml;q=0.9,'
                        'image/avif,image/webp,image/apng,*/*;q=0.8'
                    )
                }

                # Merge the random header values
                for header_name, fallback_value in header_mapping.items():
                    value = random_browser_header.get(header_name, fallback_value)
                    request.headers[header_name] = value
            else:
                # Fallback if no valid headers were fetched
                request.headers['User-Agent'] = (
                    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                    'AppleWebKit/537.36 (KHTML, like Gecko) '
                    'Chrome/120.0.0.0 Safari/537.36'
                )
                request.headers['Accept'] = (
                    'text/html,application/xhtml+xml,application/xml;q=0.9,'
                    'image/avif,image/webp,image/apng,*/*;q=0.8'
                )
                request.headers['Accept-Language'] = 'en-US,en;q=0.9'
                request.headers['Accept-Encoding'] = 'gzip, deflate, br'
        return None


###############################################################################
# 4) AUTHENTICATED PROXY MIDDLEWARE (WEBSHARE/OXYLABS)
###############################################################################
class AuthenticatedProxyMiddleware:
    """
    Middleware for handling authenticated proxies from Webshare and Oxylabs.
    - Webshare proxy list is fetched from a URL; each line contains 'ip:port:username:password'.
    - Oxylabs is used as a fallback if desired.
    """

    @classmethod
    def from_crawler(cls, crawler):
        middleware = cls(crawler.settings)
        crawler.signals.connect(middleware.spider_opened, signal=signals.spider_opened)
        crawler.signals.connect(middleware.spider_closed, signal=signals.spider_closed)
        return middleware

    def __init__(self, settings):
        # Webshare settings
        self.webshare_url = settings.get('WEBSHARE_PROXY_URL')
        self.webshare_username = settings.get('WEBSHARE_USERNAME', 'ztvwtfkm')
        self.webshare_password = settings.get('WEBSHARE_PASSWORD', 'n3y45ceo8tfx')

        # Oxylabs settings
        self.oxylabs_proxy = settings.get('OXYLABS_PROXY', 'dc.oxylabs.io:8000')
        self.oxylabs_username = settings.get('OXYLABS_USERNAME', 'user-dishpal_znLHy-country-US')
        self.oxylabs_password = settings.get('OXYLABS_PASSWORD')

        # Proxy management
        self.webshare_proxies = []
        self.current_index = 0
        self.use_oxylabs_fallback = settings.get('USE_OXYLABS_FALLBACK', True)

        # Stats
        self.stats = {
            'webshare_requests': 0,
            'oxylabs_requests': 0,
            'failed_requests': 0
        }

        # Add proxy health tracking
        self.proxy_health = {
            'webshare': {'success': 0, 'failure': 0},
            'oxylabs': {'success': 0, 'failure': 0}
        }
        self.consecutive_failures = 0
        self.max_consecutive_failures = settings.get('MAX_CONSECUTIVE_FAILURES', 3)

    def spider_opened(self, spider):
        """Initialize proxy list when spider starts."""
        self.load_webshare_proxies(spider)

    def load_webshare_proxies(self, spider):
        """Load and parse Webshare proxies from the configured URL."""
        try:
            response = requests.get(self.webshare_url, timeout=10, verify=False)
            if response.status_code == 200:
                proxies = []
                for line in response.text.strip().split():
                    parts = line.split(':')
                    if len(parts) == 4:
                        proxy = {
                            'host': parts[0],
                            'port': parts[1],
                            'username': parts[2],
                            'password': parts[3]
                        }
                        proxies.append(proxy)
                self.webshare_proxies = proxies
                spider.logger.info(f"Loaded {len(proxies)} Webshare proxies.")
            else:
                spider.logger.error(f"Failed to load Webshare proxies: status code {response.status_code}")
        except Exception as err:
            spider.logger.error(f"Error loading Webshare proxies: {str(err)}")

    def get_next_webshare_proxy(self):
        """Round-robin approach to picking the next Webshare proxy."""
        if not self.webshare_proxies:
            return None
        proxy = self.webshare_proxies[self.current_index]
        self.current_index = (self.current_index + 1) % len(self.webshare_proxies)
        return (
            f"http://{proxy['username']}:{proxy['password']}@"
            f"{proxy['host']}:{proxy['port']}"
        )

    def get_oxylabs_proxy(self):
        """Build Oxylabs proxy string with authentication."""
        if not self.oxylabs_password:
            return None
        try:
            return (
                f"http://{self.oxylabs_username}:{self.oxylabs_password}@{self.oxylabs_proxy}"
            )
        except Exception:
            return None

    def process_request(self, request, spider):
        """Assign a proxy to the request with better error handling."""
        try:
            # Try Webshare first
            if self.webshare_proxies:
                proxy = self.get_next_webshare_proxy()
                if proxy:
                    request.meta['proxy'] = proxy
                    request.meta['proxy_source'] = 'webshare'
                    self.stats['webshare_requests'] += 1
                    spider.logger.debug(f"Using Webshare proxy for {request.url}")
                    return None

            # Fallback to Oxylabs if enabled
            if self.use_oxylabs_fallback and self.oxylabs_password:
                proxy = self.get_oxylabs_proxy()
                if proxy:
                    request.meta['proxy'] = proxy
                    request.meta['proxy_source'] = 'oxylabs'
                    self.stats['oxylabs_requests'] += 1
                    spider.logger.debug(f"Using Oxylabs proxy for {request.url}")
                return None

        except Exception as e:
            spider.logger.error(f"Error assigning proxy: {str(e)}")
            return None

    def process_response(self, request, response, spider):
        """Track proxy performance and handle failures."""
        if 'proxy' in request.meta:
            proxy_source = request.meta.get('proxy_source')
            
            if response.status == 200:
                # Success case
                self.proxy_health[proxy_source]['success'] += 1
                self.consecutive_failures = 0
            else:
                # Failure case
                self.stats['failed_requests'] += 1
                self.proxy_health[proxy_source]['failure'] += 1
                self.consecutive_failures += 1
                
                spider.logger.warning(
                    f"Proxy {proxy_source} failed with status {response.status}. "
                    f"Health: {self.proxy_health[proxy_source]}"
                )
                
                # Switch to Oxylabs after too many failures
                if (proxy_source == 'webshare' and 
                    self.consecutive_failures >= self.max_consecutive_failures):
                    spider.logger.info("Switching to Oxylabs due to consecutive failures")
                    self.use_oxylabs_fallback = True
                
        return response

    def process_exception(self, request, exception, spider):
        """Handle proxy exceptions with retry logic."""
        if 'proxy' in request.meta:
            proxy_source = request.meta.get('proxy_source')
            self.stats['failed_requests'] += 1
            self.proxy_health[proxy_source]['failure'] += 1
            
            spider.logger.error(
                f"Proxy {proxy_source} failed with exception: {type(exception).__name__}"
            )
            
            # Create a new request without the failed proxy
            new_request = request.copy()
            new_request.dont_filter = True
            
            if proxy_source == 'webshare':
                # Try another Webshare proxy first
                if len(self.webshare_proxies) > 1:
                    self.current_index = (self.current_index + 1) % len(self.webshare_proxies)
                    return new_request
                # Fall back to Oxylabs if available
                elif self.use_oxylabs_fallback and self.oxylabs_password:
                    new_request.meta['proxy'] = self.get_oxylabs_proxy()
                    new_request.meta['proxy_source'] = 'oxylabs'
                    return new_request
                
        return None

    def report_stats(self, spider):
        """Report proxy usage statistics."""
        spider.logger.info("Proxy Statistics:")
        spider.logger.info(f"Webshare requests: {self.stats['webshare_requests']}")
        spider.logger.info(f"Oxylabs requests: {self.stats['oxylabs_requests']}")
        spider.logger.info(f"Failed requests: {self.stats['failed_requests']}")
        
        for source, health in self.proxy_health.items():
            success_rate = 0
            total = health['success'] + health['failure']
            if total > 0:
                success_rate = (health['success'] / total) * 100
            spider.logger.info(
                f"{source.title()} health - "
                f"Success rate: {success_rate:.2f}% "
                f"({health['success']}/{total} requests)"
            )

    def spider_closed(self, spider):
        """Report stats when spider closes."""
        self.report_stats(spider)
