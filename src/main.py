"""
Apify Store Actor: E-Commerce Product Price, Stock Status & JSON-LD Schema Extractor
Extracts structured product titles, prices, currencies, stock availability, and URLs
from Schema.org Product JSON-LD, OpenGraph tags, and universal e-commerce HTML cards.
"""
import asyncio
import json
import os
import re
from urllib.parse import urljoin
from typing import Dict, List, Any, Optional

FREE_TIER_MAX_ITEMS = 25
FREE_TIER_CAP_MSG = (
    "Free-tier run capped at 25 results. Upgrade Apify plan for unlimited scale "
    "or contact Trung Thanh Tran on Upwork for custom pipelines."
)


def is_free_tier_at_home() -> bool:
    is_at_home = os.getenv("APIFY_IS_AT_HOME", "").strip().lower() in ("1", "true", "yes")
    user_is_paying = os.getenv("APIFY_USER_IS_PAYING", "").strip().lower() in ("1", "true", "yes")
    return is_at_home and not user_is_paying

import httpx
from bs4 import BeautifulSoup

try:
    from apify import Actor
    HAS_APIFY = True
except ImportError:
    HAS_APIFY = False

PRICE_REGEX = re.compile(r"([£$€¥]|USD|EUR|GBP|VND)?\s*(\d{1,6}(?:[.,]\d{2,3})?)")


def parse_price_and_currency(raw_text: str) -> tuple[Optional[float], str]:
    if not raw_text:
        return None, "USD"
    m = PRICE_REGEX.search(raw_text)
    if not m:
        return None, "USD"
    sym = (m.group(1) or "$").upper()
    currency_map = {"$": "USD", "£": "GBP", "€": "EUR", "¥": "JPY"}
    currency = currency_map.get(sym, sym if len(sym) == 3 else "USD")
    num_str = m.group(2).replace(",", "")
    try:
        return float(num_str), currency
    except ValueError:
        return None, currency


def extract_json_ld_products(soup: BeautifulSoup, page_url: str) -> List[Dict[str, Any]]:
    records: List[Dict[str, Any]] = []
    for tag in soup.find_all("script", attrs={"type": "application/ld+json"}):
        try:
            payload = json.loads(tag.string or "{}")
            items = payload if isinstance(payload, list) else [payload]
            for item in items:
                if not isinstance(item, dict):
                    continue
                if str(item.get("@type", "")).lower() == "product":
                    offers = item.get("offers") or {}
                    if isinstance(offers, list) and offers:
                        offers = offers[0]
                    price_val = offers.get("price")
                    currency = offers.get("priceCurrency") or "USD"
                    avail_raw = str(offers.get("availability") or "InStock")
                    avail = "In Stock" if "instock" in avail_raw.lower() else "Out of Stock"
                    records.append({
                        "product_title": str(item.get("name") or "").strip(),
                        "price_amount": float(price_val) if price_val is not None else None,
                        "currency": str(currency),
                        "availability": avail,
                        "sku": str(item.get("sku") or ""),
                        "product_url": urljoin(page_url, str(offers.get("url") or page_url)),
                        "source_page_url": page_url,
                        "extraction_method": "Schema.org Product JSON-LD",
                    })
        except Exception:
            continue
    return records


def extract_html_product_cards(soup: BeautifulSoup, page_url: str, max_items: int = 25) -> List[Dict[str, Any]]:
    records: List[Dict[str, Any]] = []
    cards = soup.select("article.product_pod, div.product, li.product, div.product-card, div.grid-product")
    for card in cards[:max_items]:
        title_el = card.select_one("h3 a, h2 a, .product-title, .woocommerce-loop-product__title")
        price_el = card.select_one(".price_color, .price, .product-price, .money")
        avail_el = card.select_one(".availability, .stock, .in-stock")

        title = ""
        link = page_url
        if title_el:
            title = (title_el.get("title") or title_el.get_text(" ", strip=True) or "").strip()
            if title_el.get("href"):
                link = urljoin(page_url, title_el["href"])

        price_text = price_el.get_text(" ", strip=True) if price_el else ""
        price_amount, currency = parse_price_and_currency(price_text)
        avail_text = avail_el.get_text(" ", strip=True) if avail_el else "In Stock"
        avail = "Out of Stock" if "out" in avail_text.lower() else "In Stock"

        if title:
            records.append({
                "product_title": title,
                "price_amount": price_amount,
                "currency": currency,
                "availability": avail,
                "sku": "",
                "product_url": link,
                "source_page_url": page_url,
                "extraction_method": "HTML Product Card Parser",
            })

    if not records:
        main_title = soup.select_one("div.product_main h1, h1.product_title, h1")
        main_price = soup.select_one("div.product_main p.price_color, p.price, .product-single__price")
        if main_title and main_price:
            p_val, curr = parse_price_and_currency(main_price.get_text(" ", strip=True))
            records.append({
                "product_title": main_title.get_text(" ", strip=True),
                "price_amount": p_val,
                "currency": curr,
                "availability": "In Stock",
                "sku": "",
                "product_url": page_url,
                "source_page_url": page_url,
                "extraction_method": "Single Product Detail Parser",
            })

    return records


async def scrape_ecommerce_url(client: httpx.AsyncClient, url: str, max_items: int = 25) -> List[Dict[str, Any]]:
    try:
        resp = await client.get(url)
        if resp.status_code != 200:
            return []
        soup = BeautifulSoup(resp.text, "html.parser")
        json_ld_items = extract_json_ld_products(soup, str(resp.url))
        if json_ld_items:
            return json_ld_items[:max_items]
        return extract_html_product_cards(soup, str(resp.url), max_items=max_items)
    except Exception:
        return []


async def main() -> None:
    headers = {
        "User-Agent": "Mozilla/5.0 (compatible; ECommercePriceMonitorBot/1.0; +https://github.com/Tthanh2k6)"
    }
    if HAS_APIFY:
        async with Actor:
            actor_input = await Actor.get_input() or {}
            raw_urls = actor_input.get("startUrls") or [
                {"url": "https://books.toscrape.com/catalogue/category/books/travel_2/index.html"},
                {"url": "https://books.toscrape.com/catalogue/a-light-in-the-attic_1000/index.html"},
            ]
            max_items_per_page = int(actor_input.get("maxItemsPerPage", 25))
            max_items = int(actor_input.get("maxItems", 25))
            urls = [item["url"] if isinstance(item, dict) else str(item) for item in raw_urls if item]

            was_capped = False
            if is_free_tier_at_home() and (
                max_items > FREE_TIER_MAX_ITEMS
                or max_items_per_page > FREE_TIER_MAX_ITEMS
                or len(urls) > FREE_TIER_MAX_ITEMS
            ):
                max_items = min(max_items, FREE_TIER_MAX_ITEMS)
                max_items_per_page = min(max_items_per_page, FREE_TIER_MAX_ITEMS)
                urls = urls[:FREE_TIER_MAX_ITEMS]
                was_capped = True
                Actor.log.warning(FREE_TIER_CAP_MSG)
                await Actor.set_status_message(FREE_TIER_CAP_MSG)

            all_products: List[Dict[str, Any]] = []
            async with httpx.AsyncClient(headers=headers, timeout=12.0, follow_redirects=True) as client:
                for u in urls:
                    remaining = max_items - len(all_products)
                    if remaining <= 0:
                        break
                    items = await scrape_ecommerce_url(client, u, max_items=min(max_items_per_page, remaining))
                    all_products.extend(items)

            if is_free_tier_at_home() and len(all_products) > FREE_TIER_MAX_ITEMS:
                all_products = all_products[:FREE_TIER_MAX_ITEMS]
                was_capped = True

            await Actor.push_data(all_products)
            if was_capped:
                await Actor.set_status_message(FREE_TIER_CAP_MSG)
            else:
                await Actor.set_status_message(f"Extracted {len(all_products)} e-commerce product records.")
            Actor.log.info(f"Extracted and pushed {len(all_products)} e-commerce product records.")
    else:
        sample_urls = [
            "https://books.toscrape.com/catalogue/category/books/travel_2/index.html",
            "https://books.toscrape.com/catalogue/a-light-in-the-attic_1000/index.html",
        ]
        all_products = []
        async with httpx.AsyncClient(headers=headers, timeout=15.0, follow_redirects=True) as client:
            for u in sample_urls:
                all_products.extend(await scrape_ecommerce_url(client, u, max_items=10))
        print(f"Extracted {len(all_products)} sample products.")
        print(json.dumps(all_products[:3], indent=2))

