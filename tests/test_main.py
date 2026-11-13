import pathlib
import sys
from unittest.mock import AsyncMock, MagicMock

import pytest
from bs4 import BeautifulSoup

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from src.main import (
    _coerce_positive_int,
    _extract_start_urls,
    extract_html_product_cards,
    extract_json_ld_products,
    parse_price_and_currency,
    scrape_ecommerce_url,
)


def test_parse_price_and_currency():
    assert parse_price_and_currency("£45.17") == (45.17, "GBP")
    assert parse_price_and_currency("€19.99") == (19.99, "EUR")
    assert parse_price_and_currency("$1,250") == (1250.0, "USD")
    assert parse_price_and_currency("VND 250000") == (250000.0, "VND")
    assert parse_price_and_currency("") == (None, "USD")
    assert parse_price_and_currency("Contact for quote") == (None, "USD")


def test_coerce_positive_int_handles_null_and_bad_values():
    assert _coerce_positive_int(None, 25) == 25
    assert _coerce_positive_int(True, 25) == 25
    assert _coerce_positive_int(0, 25) == 25
    assert _coerce_positive_int(-3, 25) == 25
    assert _coerce_positive_int("not-a-number", 25) == 25
    assert _coerce_positive_int("12", 25) == 12
    assert _coerce_positive_int(8, 25) == 8


def test_extract_start_urls_skips_malformed_items():
    raw = [
        {},
        {"url": ""},
        {"url": None},
        {"url": "  https://example.com/p1  "},
        "https://example.com/p2",
        None,
    ]
    assert _extract_start_urls(raw) == [
        "https://example.com/p1",
        "https://example.com/p2",
    ]
    assert _extract_start_urls([]) == []


def test_extract_json_ld_products_and_edge_offers():
    html = """
    <html><head>
      <script type="application/ld+json">
        {"@type":"Product","name":"Mechanical Keyboard","sku":"KB-01",
         "offers":{"price":"129.50","priceCurrency":"USD","availability":"https://schema.org/InStock","url":"/kb-01"}}
      </script>
      <script type="application/ld+json">
        {"@type":"Product","name":"Out Item","offers":[]}
      </script>
      <script type="application/ld+json">
        {"@type":"Product","name":"Bad Price","offers":{"price":"N/A","availability":"OutOfStock"}}
      </script>
    </head></html>
    """
    soup = BeautifulSoup(html, "html.parser")
    rows = extract_json_ld_products(soup, "https://shop.example/cat")
    assert len(rows) == 3
    assert rows[0]["product_title"] == "Mechanical Keyboard"
    assert rows[0]["price_amount"] == 129.5
    assert rows[0]["availability"] == "In Stock"
    assert rows[0]["product_url"] == "https://shop.example/kb-01"
    assert rows[1]["price_amount"] is None
    assert rows[2]["price_amount"] is None
    assert rows[2]["availability"] == "Out of Stock"


def test_extract_html_product_cards_and_single_fallback():
    cards_html = """
    <html><body>
      <article class="product_pod">
        <h3><a href="book1.html" title="Book One">Book One</a></h3>
        <p class="price_color">£12.34</p>
        <p class="availability">In stock</p>
      </article>
      <article class="product_pod">
        <h3><a href="book2.html" title="Book Two">Book Two</a></h3>
        <p class="price_color">£20.00</p>
        <p class="availability">Out of stock</p>
      </article>
    </body></html>
    """
    rows = extract_html_product_cards(
        BeautifulSoup(cards_html, "html.parser"), "https://books.example/cat/", max_items=1
    )
    assert len(rows) == 1
    assert rows[0]["product_title"] == "Book One"
    assert rows[0]["extraction_method"] == "HTML Product Card Parser"

    single_html = """
    <html><body>
      <div class="product_main"><h1>Solo Item</h1><p class="price_color">$49.00</p></div>
    </body></html>
    """
    single_rows = extract_html_product_cards(
        BeautifulSoup(single_html, "html.parser"), "https://shop.example/solo"
    )
    assert len(single_rows) == 1
    assert single_rows[0]["extraction_method"] == "Single Product Detail Parser"
    assert single_rows[0]["price_amount"] == 49.0


def test_scrape_ecommerce_url_handles_non_200_and_200():
    import asyncio

    client = MagicMock()
    resp_404 = MagicMock(status_code=404, text="", url="https://shop.example/missing")
    client.get = AsyncMock(return_value=resp_404)
    assert asyncio.run(scrape_ecommerce_url(client, "https://shop.example/missing")) == []

    resp_200 = MagicMock(
        status_code=200,
        text='<div class="product_main"><h1>Mug</h1><p class="price_color">$15.00</p></div>',
        url="https://shop.example/mug",
    )
    client.get = AsyncMock(return_value=resp_200)
    res = asyncio.run(scrape_ecommerce_url(client, "https://shop.example/mug"))
    assert len(res) == 1
    assert res[0]["product_title"] == "Mug"
