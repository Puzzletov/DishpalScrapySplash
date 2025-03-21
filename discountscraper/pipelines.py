# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface

from itemadapter import ItemAdapter
from datetime import datetime

class DiscountPipeline:
    """Pipeline to clean and standardize discount data"""
    
    def process_item(self, item, spider):
        adapter = ItemAdapter(item)
        
        # Clean prices
        price_fields = ['original_price', 'sale_price', 'price_per_unit']
        for field in price_fields:
            value = adapter.get(field)
            if value:
                try:
                    # Remove currency symbol and convert to float
                    cleaned_price = value.replace('€', '').replace(',', '.').strip()
                    adapter[field] = float(cleaned_price)
                except (ValueError, TypeError):
                    adapter[field] = None
        
        # Clean discount percentage
        discount = adapter.get('discount_percentage')
        if discount:
            try:
                # Remove % and - signs, convert to positive integer
                cleaned_discount = discount.replace('%', '').replace('-', '').strip()
                adapter['discount_percentage'] = int(cleaned_discount)
            except (ValueError, TypeError):
                adapter['discount_percentage'] = None
        
        # Add timestamp
        adapter['timestamp'] = datetime.now().isoformat()
        
        return item
