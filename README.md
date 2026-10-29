# E-Commerce Product Price, Stock Status & JSON-LD Schema Extractor (Apify Actor)

Fast, low-memory **Python Async (`httpx` + `BeautifulSoup4`) Apify Actor** that extracts structured product titles, prices, currencies, stock availability (`In Stock` / `Out of Stock`), SKUs, and product URLs from Shopify, WooCommerce, and custom e-commerce catalogs.

## ✨ Key Features

- **Dual Extraction Engine:** Automatically parses `Schema.org Product JSON-LD` first, then falls back to universal HTML product card and single-product detail selectors.
- **Currency & Price Normalization:** Parses numeric prices alongside ISO currency codes (`USD`, `GBP`, `EUR`, `JPY`, `VND`).
- **Stock Availability Tracking:** Detects `In Stock` vs. `Out of Stock` status for automated inventory monitoring.
- **Zero Headless Browser Overhead:** Runs on pure async `httpx` (`< 25 MB` RAM) for maximum speed and minimal Apify Compute Units.

## 👤 Author

**Trung Thanh Tran** — [Hire me on Upwork](https://www.upwork.com/freelancers/trungthanhtrandev) | [GitHub](https://github.com/Tthanh2k6)
