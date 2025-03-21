# Scrapy settings for bookscraper project
#
# For simplicity, this file contains only settings considered important or
# commonly used. You can find more settings consulting the documentation:
#
#     https://docs.scrapy.org/en/latest/topics/settings.html
#     https://docs.scrapy.org/en/latest/topics/downloader-middleware.html
#     https://docs.scrapy.org/en/latest/topics/spider-middleware.html


###############################################################################
# CORE SETTINGS
###############################################################################

BOT_NAME = "discountscraper"
SPIDER_MODULES = ["discountscraper.spiders"]
NEWSPIDER_MODULE = "discountscraper.spiders"

###############################################################################
# FEEDS & OUTPUT
###############################################################################

FEEDS = {
    'discounts.json': {'format': 'json'}
}
FEED_EXPORT_ENCODING = "utf-8"

###############################################################################
# SCRAPEOPS BROWSER HEADERS
###############################################################################

SCRAPEOPS_API_KEY = '34da501f-2d6f-4797-83fc-dd322afe9146'
SCRAPEOPS_BROWSER_HEADERS_ENDPOINT = 'https://headers.scrapeops.io/v1/browser-headers'
SCRAPEOPS_BROWSER_HEADERS_ENABLED = True
SCRAPEOPS_NUM_RESULTS = 50

###############################################################################
# AUTHENTICATED PROXY SETTINGS
###############################################################################

# Webshare Proxy Settings
WEBSHARE_PROXY_URL = 'https://proxy.webshare.io/api/v2/proxy/list/download/jmdzgvsdvgdbflhggqklwgmbpevfugpwhgtttvmi/-/any/username/direct/-/'
WEBSHARE_USERNAME = 'ztvwtfkm'
WEBSHARE_PASSWORD = 'n3y45ceo8tfx'

# Oxylabs Proxy Settings
OXYLABS_PROXY = 'dc.oxylabs.io:8000'
OXYLABS_USERNAME = 'user-dishpal_znLHy-country-US'
OXYLABS_PASSWORD = 'KelvinEgbine_92'  # Replace with actual password
USE_OXYLABS_FALLBACK = True

###############################################################################
# PERFORMANCE & THROTTLING
###############################################################################

# Request settings
DOWNLOAD_TIMEOUT = 30
DOWNLOAD_DELAY = 3
CONCURRENT_REQUESTS = 2
CONCURRENT_REQUESTS_PER_DOMAIN = 2

# Retry configuration
RETRY_ENABLED = True
RETRY_TIMES = 3
RETRY_HTTP_CODES = [500, 502, 503, 504, 522, 524, 408, 429]

# AutoThrottle
AUTOTHROTTLE_ENABLED = True
AUTOTHROTTLE_START_DELAY = 1
AUTOTHROTTLE_MAX_DELAY = 60
AUTOTHROTTLE_TARGET_CONCURRENCY = 1.0

###############################################################################
# MIDDLEWARE CONFIGURATION
###############################################################################

DOWNLOADER_MIDDLEWARES = {
    'scrapy_splash.SplashCookiesMiddleware': 723,
    'scrapy_splash.SplashMiddleware': 725,
    'scrapy.downloadermiddlewares.httpcompression.HttpCompressionMiddleware': 810,
    'discountscraper.middlewares.ScrapeOpsFakeBrowserHeaderMiddleware': 400,
}

###############################################################################
# PIPELINES
###############################################################################

ITEM_PIPELINES = {
    'discountscraper.pipelines.DiscountPipeline': 300,
}

###############################################################################
# SECURITY & PROTECTION
###############################################################################

ROBOTSTXT_OBEY = False
COOKIES_ENABLED = False
REFERRER_POLICY = 'same-origin'

###############################################################################
# MISC & SYSTEM
###############################################################################

TWISTED_REACTOR = "twisted.internet.asyncioreactor.AsyncioSelectorReactor"

# Crawl responsibly by identifying yourself
USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'

# Enable logging of retry middleware
RETRY_ENABLED = True
LOG_LEVEL = 'INFO'

# Add Splash Configuration
SPLASH_URL = 'http://localhost:8050'
SPLASH_COOKIES_DEBUG = True
SPLASH_LOG_400 = True

# Update Middleware Settings
SPIDER_MIDDLEWARES = {
    'scrapy_splash.SplashDeduplicateArgsMiddleware': 100,
}

# Performance Settings
DOWNLOAD_DELAY = 3
CONCURRENT_REQUESTS = 2
CONCURRENT_REQUESTS_PER_DOMAIN = 2
RANDOMIZE_DOWNLOAD_DELAY = True
