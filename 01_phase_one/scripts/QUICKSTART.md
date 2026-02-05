# Scraper Quick Start Guide

## Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Start required services
cd .. && docker compose up -d

# Verify installation
python test_scraper.py
```

## Basic Usage

### Command Line

```bash
# Simple scrape
python scraper.py https://example.com

# Save to file
python scraper.py https://example.com -o result.json

# Quiet mode
python scraper.py https://example.com -q

# Verbose mode
python scraper.py https://example.com -v
```

### Python API

```python
from scraper import scrape

# Basic usage
result = scrape("https://example.com")

if result["result"]["success"]:
    content = result["result"]["content"]
    print(f"Success! Got {len(content)} chars")
else:
    print(f"Failed: {result['result']['error']}")
```

## Layer Control

```bash
# Force specific layer
python scraper.py https://example.com --layer 1  # curl_cffi
python scraper.py https://example.com --layer 2  # Firecrawl
python scraper.py https://example.com --layer 3  # FlareSolverr
```

## Proxy Control

```bash
# Force proxy
python scraper.py https://example.com --proxy

# Force no proxy
python scraper.py https://example.com --no-proxy
```

## Programmatic Usage

```python
from scraper import scrape

# Force layer
result = scrape(url, force_layer=2)

# Force proxy
result = scrape(url, force_proxy=True)

# Quiet mode
result = scrape(url, quiet=True)

# Combined
result = scrape(
    "https://example.com",
    force_layer=2,
    force_proxy=True,
    quiet=True
)
```

## Output Format

```json
{
  "url": "https://example.com",
  "timestamp": "2026-02-01T12:00:00Z",
  "result": {
    "success": true,
    "content": "<html>...</html>",
    "method": "curl_cffi",
    "status_code": 200,
    "error": null,
    "elapsed": 0.85,
    "challenge_detected": false
  },
  "total_elapsed": 0.92,
  "attempts": [...]
}
```

## Troubleshooting

### Services Not Running

```bash
# Check service status
docker compose ps

# View logs
docker compose logs firecrawl
docker compose logs flaresolverr
docker compose logs tor-proxy

# Restart services
docker compose restart
```

### curl_cffi Not Available

```bash
# Install curl_cffi
pip install curl_cffi>=0.7.0

# Or continue without it (starts at Layer 2)
# No action needed - scraper will skip Layer 1
```

### All Layers Fail

```bash
# Run with verbose logging
python scraper.py https://example.com -v

# Test each layer individually
python scraper.py https://example.com --layer 1
python scraper.py https://example.com --layer 2
python scraper.py https://example.com --layer 3
```

## Common Patterns

### Batch Processing

```python
urls = ["https://example.com", "https://example.org"]

for url in urls:
    result = scrape(url, quiet=True)
    if result["result"]["success"]:
        # Process content
        pass
```

### Error Handling

```python
result = scrape(url)

if not result["result"]["success"]:
    error = result["result"]["error"]
    attempts = len(result["attempts"])
    print(f"Failed after {attempts} attempts: {error}")
```

### Content Extraction

```python
import re

result = scrape(url)
if result["result"]["success"]:
    html = result["result"]["content"]

    # Extract title
    title = re.search(r'<title>(.*?)</title>', html)
    if title:
        print(f"Title: {title.group(1)}")
```

## Performance Tips

1. **Use site profiles** - Add frequently scraped domains to `SITE_PROFILES`
2. **Skip unnecessary layers** - Use `--layer` if you know site requirements
3. **Avoid proxy when possible** - Proxy adds latency
4. **Batch with delays** - Add `time.sleep()` between requests to same domain
5. **Monitor attempts** - Track which layers succeed for optimization

## Security Notes

- Scraping may violate site terms of service
- Use Tor for IP rotation, not guaranteed anonymity
- Implement your own rate limiting for production
- Respect robots.txt and site policies
- Consider legal implications in your jurisdiction

## Next Steps

- Read full documentation: `README.md`
- Review implementation details: `IMPLEMENTATION.md`
- Check usage examples: `example_usage.py`
- Run test suite: `python test_scraper.py`

## Quick Reference

| Command | Description |
|---------|-------------|
| `python scraper.py URL` | Basic scrape |
| `python scraper.py URL -o file.json` | Save to file |
| `python scraper.py URL -q` | Quiet mode |
| `python scraper.py URL -v` | Verbose mode |
| `python scraper.py URL --layer N` | Force layer 1-3 |
| `python scraper.py URL --proxy` | Force proxy |
| `python scraper.py URL --no-proxy` | Force no proxy |

| Layer | Method | Best For |
|-------|--------|----------|
| 1 | curl_cffi | Fast, unprotected sites |
| 2 | Firecrawl | JavaScript-heavy sites |
| 3 | FlareSolverr | Cloudflare challenges |

| File | Purpose |
|------|---------|
| `scraper.py` | Main implementation |
| `test_scraper.py` | Test suite |
| `example_usage.py` | Usage examples |
| `requirements.txt` | Dependencies |
| `README.md` | Full documentation |
| `IMPLEMENTATION.md` | Technical details |
| `QUICKSTART.md` | This guide |
