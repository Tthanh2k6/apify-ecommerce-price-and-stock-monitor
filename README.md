# E-Commerce Product Price, Stock Status and JSON-LD Extractor (Apify Actor)

An Apify actor in async Python (`httpx` + `BeautifulSoup4`). For each product or category URL you give it, it fetches the page once and returns product title, price, currency, availability, SKU and product URL.

## How extraction works

1. **Schema.org JSON-LD first.** If the page has a `Product` JSON-LD block, it reads `name`, `sku` and the first entry in `offers` (`price`, `priceCurrency`, `availability`, `url`). Availability becomes `In Stock` if the value contains `InStock`, otherwise `Out of Stock`. Only the first offer is read, so there is no per-variant price or stock.
2. **HTML product cards next.** If there is no JSON-LD product, it looks for common card selectors (`article.product_pod`, `div.product`, `li.product`, `div.product-card`, `div.grid-product`) and reads title, link, price text and a stock element. If a card has no stock element, it is reported as `In Stock`.
3. **Single product page last.** If no cards are found, it tries a `h1` plus a price element.

Prices are parsed with a regex that recognizes `$`, `£`, `€`, `¥`, `USD`, `EUR`, `GBP` and `VND`. Anything else defaults to `USD`. Each record has an `extraction_method` field so you can see which step produced it.

Pages that return a non-200 status or fail to load produce no records. The actor does not use a headless browser, does not follow pagination, and does not store history between runs. To monitor changes over time, schedule it on Apify and compare datasets yourself.

## Input

```json
{
  "startUrls": [
    { "url": "https://books.toscrape.com/catalogue/category/books/travel_2/index.html" },
    { "url": "https://books.toscrape.com/catalogue/a-light-in-the-attic_1000/index.html" }
  ],
  "maxItemsPerPage": 25,
  "maxItems": 25
}
```

Runs on the Apify free tier are capped at 25 results.

## Output record

```json
{
  "product_title": "It's Only the Himalayas",
  "price_amount": 45.17,
  "currency": "GBP",
  "availability": "In Stock",
  "sku": "",
  "product_url": "https://books.toscrape.com/catalogue/its-only-the-himalayas_981/index.html",
  "source_page_url": "https://books.toscrape.com/catalogue/category/books/travel_2/index.html",
  "extraction_method": "HTML Product Card Parser"
}
```

## Calling it from Python

```python
from apify_client import ApifyClient

client = ApifyClient("YOUR_APIFY_TOKEN")
run = client.actor("thanh81646/apify-ecommerce-price-and-stock-monitor").call(
    run_input={"startUrls": [{"url": "https://books.toscrape.com/catalogue/category/books/travel_2/index.html"}]}
)
for item in client.dataset(run["defaultDatasetId"]).iterate_items():
    print(item)
```

In n8n or Make.com, use the Apify "Run an Actor" node/module with the actor ID `thanh81646/apify-ecommerce-price-and-stock-monitor`.

## Author

Trung Thanh Tran: [Upwork](https://www.upwork.com/freelancers/trungthanhtrandev) · [GitHub](https://github.com/Tthanh2k6) · [Apify](https://apify.com/thanh81646)

## Legal note

The actor reads public product pages at the user's direction. It is not affiliated with Shopify, WooCommerce or any retailer; trademarks belong to their owners. It does not bypass logins or access controls. You are responsible for complying with each site's terms, rate limits and applicable law.
