# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
from itemadapter import ItemAdapter


class BookscraperPipeline:
    def process_item(self, item, spider):

        adapter = ItemAdapter(item)

        ## Strip all whitespaces from strings
        field_names = adapter.field_names()
        for field_name in field_names:
            if field_name != 'description':
                value = adapter.get(field_name)
                adapter[field_name] = value[0].strip()


        ## Category & Product Type --> switch to lowercase
        lowercase_keys = ['category', 'product_type']
        for lowercase_key in lowercase_keys:
            value = adapter.get(lowercase_key)
            adapter[lowercase_key] = value.lower()



        ## Price --> convert to float
        price_keys = ['price', 'price_excl_tax', 'price_incl_tax', 'tax']
        for price_key in price_keys:
            value = adapter.get(price_key)
            value = value.replace('£', '')
            adapter[price_key] = float(value)


        ## Availability --> extract number of books in stock
        availability_string = adapter.get('availability')
        split_string_array = availability_string.split('(')
        if len(split_string_array) < 2:
            adapter['availability'] = 0
        else:
            availability_array = split_string_array[1].split(' ')
            adapter['availability'] = int(availability_array[0])



        ## Reviews --> convert string to number
        num_reviews_string = adapter.get('num_reviews')
        adapter['num_reviews'] = int(num_reviews_string)


        ## Stars --> convert text to number
        stars_string = adapter.get('stars')
        split_stars_array = stars_string.split(' ')
        stars_text_value = split_stars_array[1].lower()
        if stars_text_value == "zero":
            adapter['stars'] = 0
        elif stars_text_value == "one":
            adapter['stars'] = 1
        elif stars_text_value == "two":
            adapter['stars'] = 2
        elif stars_text_value == "three":
            adapter['stars'] = 3
        elif stars_text_value == "four":
            adapter['stars'] = 4
        elif stars_text_value == "five":
            adapter['stars'] = 5


        return item


#cleaning myteck data 
import re

class CleanMytekPipeline:

    def process_item(self, item, spider):

        # ---- Clean Title ----
        if item.get("title"):
            item["title"] = item["title"].strip()

        # ---- Clean Price ----
        raw_price = item.get("price", "")
        # remove unicode narrow no-break space (\u202f) and normal spaces
        raw_price = raw_price.replace("\u202f", "").replace(" ", "")

        # extract numeric part
        match = re.search(r"([\d,.]+)", raw_price)
        if match:
            price_str = match.group(1).replace(",", ".")
            try:
                item["price"] = float(price_str)
            except:
                item["price"] = None
        else:
            item["price"] = None

        # extract currency (DT)
        if "DT" in raw_price.upper():
            item["price_currency"] = "DT"
        else:
            item["price_currency"] = None

        # ---- Clean SKU ----
        if item.get("sku"):
            item["sku"] = item["sku"].replace("[", "").replace("]", "").strip()

        # ---- Normalise availability ----
        if item.get("availability"):
            avail = item["availability"].lower()

            if "stock" in avail:
                item["availability"] = "In stock"
            elif "rupture" in avail or "épuisé" in avail:
                item["availability"] = "Out of stock"
            else:
                item["availability"] = "Unknown"

        # ---- Clean description ----
        if item.get("short_description"):
            desc = item["short_description"]

            desc = re.sub(r"\s+", " ", desc)  # remove newlines & excess spaces
            desc = desc.strip()
            item["short_description"] = desc

        return item

    




# postgres database for myteck spider 

import psycopg2
from psycopg2.extras import RealDictCursor


class PostgresPipeline:
    def __init__(self, pg_host, pg_db, pg_user, pg_pass, pg_port):
        self.pg_host = pg_host
        self.pg_db = pg_db
        self.pg_user = pg_user
        self.pg_pass = pg_pass
        self.pg_port = pg_port

    @classmethod
    def from_crawler(cls, crawler):
        return cls(
            pg_host=crawler.settings.get("PG_HOST"),
            pg_db=crawler.settings.get("PG_DATABASE"),
            pg_user=crawler.settings.get("PG_USER"),
            pg_pass=crawler.settings.get("PG_PASSWORD"),
            pg_port=crawler.settings.get("PG_PORT"),
        )

    def open_spider(self, spider):
        """Open PostgreSQL connection when spider opens"""
        self.conn = psycopg2.connect(
            host=self.pg_host,
            database=self.pg_db,
            user=self.pg_user,
            password=self.pg_pass,
            port=self.pg_port
        )
        self.cursor = self.conn.cursor()
        spider.logger.info("Connected to PostgreSQL successfully.")

    def close_spider(self, spider):
        """Close DB connection when spider closes"""
        self.conn.commit()
        self.cursor.close()
        self.conn.close()
        spider.logger.info("PostgreSQL connection closed.")

    def process_item(self, item, spider):
        """Insert scraped item into PostgreSQL"""

        sql = """
            INSERT INTO products (
                title, price, image, url, availability,
                short_description, category, price_currency
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (url) DO UPDATE SET
                title = EXCLUDED.title,
                price = EXCLUDED.price,
                image = EXCLUDED.image,
                availability = EXCLUDED.availability,
                short_description = EXCLUDED.short_description,
                category = EXCLUDED.category,
                price_currency = EXCLUDED.price_currency;
        """

        values = (
            item.get("title"),
            item.get("price"),
            item.get("image"),
            item.get("url"),
            item.get("availability"),
            item.get("short_description"),
            item.get("category"),
            item.get("price_currency"),
        )

        try:
            self.cursor.execute(sql, values)
            self.conn.commit()
        except Exception as e:
            spider.logger.error(f"Failed to insert item: {e}")
            self.conn.rollback()

        return item


