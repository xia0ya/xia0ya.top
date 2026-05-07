# Amazon Scraper

A Playwright-based web scraper for extracting product and review data from Amazon.

## Installation

```bash
# Clone the repository
git clone <repository-url>
cd amazon-scraper

# Install dependencies
pip install -r requirements.txt

# Install Playwright browsers
playwright install chromium
```

## Configuration

Copy `.env.example` to `.env` and configure your settings:

```bash
cp .env.example .env
```

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `PROXY_PROVIDER` | Proxy provider name (e.g., oxylabs) | - |
| `PROXY_USERNAME` | Proxy authentication username | - |
| `PROXY_PASSWORD` | Proxy authentication password | - |
| `PROXY_LIST` | Comma-separated list of proxies in format `ip:port:user:pass` | - |

## Running

```bash
# Run the scraper
python -m scraper

# Run tests
pytest
```

## Output

Scraped data is stored in `database/products.db` (SQLite database).
