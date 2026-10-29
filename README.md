# E-Commerce Product Price, Stock Status & JSON-LD Schema Extractor (Apify Actor)

Fast, low-memory **Python Async (`httpx` + `BeautifulSoup4`) Apify Actor** that extracts structured product titles, prices, currencies, stock availability (`In Stock` / `Out of Stock`), SKUs, and product URLs from Shopify, WooCommerce, and custom e-commerce catalogs.

## ✨ Key Features

- **Dual Extraction Engine:** Automatically parses `Schema.org Product JSON-LD` first, then falls back to universal HTML product card and single-product detail selectors.
- **Currency & Price Normalization:** Parses numeric prices alongside ISO currency codes (`USD`, `GBP`, `EUR`, `JPY`, `VND`).
- **Stock Availability Tracking:** Detects `In Stock` vs. `Out of Stock` status for automated inventory monitoring.
- **Zero Headless Browser Overhead:** Runs on pure async `httpx` (`< 25 MB` RAM) for maximum speed and minimal Apify Compute Units.

---

## 🛠️ Integration with n8n, Make.com & Python

### Python (pify-client)
`python
from apify_client import ApifyClient

client = ApifyClient('YOUR_APIFY_TOKEN')
run = client.actor('thanh81646/apify-ecommerce-price-and-stock-monitor').call(run_input={})
for item in client.dataset(run['defaultDatasetId']).iterate_items():
    print(item)
`

### n8n / Make.com Workflow
1. Add the official **Apify** node in **n8n** or **Make.com**.
2. Select **Run an Actor** and choose this Actor (	hanh81646/apify-ecommerce-price-and-stock-monitor).
3. Map the output Dataset items directly into **Google Sheets**, **HubSpot**, **Airtable**, **PostgreSQL / Supabase**, or **OpenAI Structured Outputs**.

---

## 💼 Need a Custom Scraper, Hidden API Extractor, or n8n / AI Workflow?

Built and maintained by **Trung Thanh Tran** (*Python, Playwright & AI Automation Developer*):
- 🚀 **Hire me on Upwork (1-Day Turnaround /  Starter Packages Available):** [upwork.com/freelancers/trungthanhtrandev](https://www.upwork.com/freelancers/trungthanhtrandev)
- 💻 **GitHub Portfolio:** [github.com/Tthanh2k6](https://github.com/Tthanh2k6)
- 🌐 **3D Interactive Portfolio:** [portfolio-red-theta-65.vercel.app](https://portfolio-red-theta-65.vercel.app/)
