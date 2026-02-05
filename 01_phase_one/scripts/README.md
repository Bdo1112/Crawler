# Production Web Scraper with 3-Layer Escalation

A production-ready Python web scraper with intelligent escalation strategy for bypassing anti-bot protections.

## Architecture

### 3-Layer Escalation Strategy

```
┌─────────────────────────────────────────────────────────────┐
│  Layer 1: curl_cffi (TLS Fingerprinting)                   │
│  - Fastest: No JS rendering                                 │
│  - Chrome TLS fingerprint                                   │
│  - Try without proxy → Try with Tor proxy                   │
└─────────────────────────────────────────────────────────────┘
                           ↓ (if blocked/challenge)
┌─────────────────────────────────────────────────────────────┐
│  Layer 2: Firecrawl API (Full Browser)                     │
│  - JavaScript execution                                     │
│  - Human behavior simulation                                │
│  - Try without proxy → Rotate Tor + Try with proxy          │
└─────────────────────────────────────────────────────────────┘
                           ↓ (if Cloudflare challenge)
┌─────────────────────────────────────────────────────────────┐
│  Layer 3: FlareSolverr (Challenge Solver)                  │
│  - Dedicated Cloudflare bypass                              │
│  - Automatic challenge solving                              │
│  - Last resort                                              │
└─────────────────────────────────────────────────────────────┘
```

## Features

### Core Capabilities

- **Smart Detection**: Automatically detects Cloudflare, PerimeterX, DataDome, and generic bot challenges
- **Content Validation**: Ensures scraped content is meaningful (not empty or blocked pages)
- **Site Profiles**: Optimizes scraping strategy based on known site patterns
- **Tor Integration**: Automatic circuit rotation for IP changes
- **Comprehensive Logging**: Detailed progress tracking and error reporting
- **Type Safety**: Full type hints for all functions and classes

### Layer Details

#### Layer 1: curl_cffi
- Uses `chrome131` TLS fingerprint
- Realistic browser headers (Accept, Sec-Fetch-*, etc.)
- Optional Tor proxy routing
- Fastest for unprotected sites (typically <1s)

#### Layer 2: Firecrawl API
- Full browser rendering via API
- JavaScript execution
- Optional human behavior simulation
- Configurable wait times (3s default)
- Returns both HTML and Markdown

#### Layer 3: FlareSolverr
- Specialized Cloudflare challenge solver
- Handles JavaScript challenges
- Automatic cookie management
- Only used when lower layers fail

## Installation

### 1. Install Python Dependencies

```bash
cd scripts
pip install -r requirements.txt
```

### 2. Ensure Services Are Running

Required services (from docker-compose.yml):
- Tor proxy on `localhost:8118`
- Tor control on `localhost:9051`
- Firecrawl API on `localhost:3002`
- FlareSolverr on `localhost:8191`

```bash
# From project root
docker compose up -d
```

### 3. Verify Installation

```bash
python test_scraper.py
```

## Usage

### Basic Usage

```bash
# Simple scrape
python scraper.py https://example.com

# Save to file
python scraper.py https://example.com -o result.json

# Quiet mode (no progress messages)
python scraper.py https://example.com -q
```

### Advanced Usage

```bash
# Force specific layer
python scraper.py https://example.com --layer 2

# Force proxy usage
python scraper.py https://example.com --proxy

# Disable proxy
python scraper.py https://example.com --no-proxy

# Verbose logging
python scraper.py https://example.com -v
```

### CLI Options

```
positional arguments:
  url                   URL to scrape

options:
  -h, --help            show this help message and exit
  -o OUTPUT, --output OUTPUT
                        Output file path (JSON format)
  -q, --quiet           Suppress progress messages
  --layer {1,2,3}       Force specific layer (1=curl_cffi, 2=firecrawl, 3=flaresolverr)
  --proxy               Force proxy usage
  --no-proxy            Force no proxy usage
  -v, --verbose         Enable verbose logging
```

## Output Format

### Success Response

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
  "attempts": [
    {
      "success": true,
      "content": "<html>...</html>",
      "method": "curl_cffi",
      "status_code": 200,
      "error": null,
      "elapsed": 0.85,
      "challenge_detected": false
    }
  ]
}
```

### Failure Response

```json
{
  "url": "https://protected-site.com",
  "timestamp": "2026-02-01T12:00:00Z",
  "result": {
    "success": false,
    "content": null,
    "method": "flaresolverr",
    "status_code": null,
    "error": "All scraping layers failed",
    "elapsed": 45.2,
    "challenge_detected": true
  },
  "total_elapsed": 48.5,
  "attempts": [...]
}
```

## Site Profiles

Predefined optimization profiles for known sites:

```python
SITE_PROFILES = {
    "zillow.com": {
        "start_layer": 2,      # Skip curl_cffi, go straight to Firecrawl
        "use_proxy": True,     # Always use Tor proxy
        "human_behavior": True # Enable human behavior simulation
    },
    "redfin.com": {
        "start_layer": 2,
        "use_proxy": True,
        "human_behavior": True
    },
    "example.com": {
        "start_layer": 1,      # Try curl_cffi first
        "use_proxy": False,    # No proxy needed
        "human_behavior": False
    }
}
```

Add custom profiles by editing `SITE_PROFILES` in `scraper.py`.

## Challenge Detection

The scraper automatically detects various anti-bot systems:

### Cloudflare
- `cf-browser-verification`
- `Just a moment...`
- `Checking your browser`
- `ray ID:`
- `__cf_chl_jschl_tk__`

### PerimeterX
- `px-captcha`
- `_px`
- `perimeterx`

### DataDome
- `datadome`
- `dd_challenge`
- `geo.captcha-delivery.com`

### Generic
- `Access denied`
- `bot detection`
- `Attention Required`

## Configuration

Edit these constants in `scraper.py` to customize:

```python
TOR_CONTROL_PORT = 9051
TOR_CONTROL_PASSWORD = ""  # Set if Tor requires authentication
TOR_PROXY_URL = "http://localhost:8118"
FIRECRAWL_API_URL = "http://localhost:3002/v1/scrape"
FLARESOLVERR_API_URL = "http://localhost:8191/v1"
```

## Tor Circuit Rotation

The scraper automatically rotates Tor circuits when needed:

```python
# Automatic rotation before retry with proxy
result = scrape("https://example.com")

# Manual rotation
from scraper import rotate_tor_circuit
rotate_tor_circuit()
```

Circuit rotation requirements:
- Tor control port open (9051)
- Control authentication configured (or disabled)
- 2-second wait after rotation for new circuit

## Error Handling

The scraper handles various failure scenarios:

1. **Network errors**: Timeouts, connection failures
2. **Challenge pages**: Detected and escalated to appropriate layer
3. **Empty content**: Validated for meaningfulness
4. **Service unavailable**: Graceful degradation to next layer
5. **API errors**: Detailed error messages in response

## Performance

### Typical Response Times

| Layer | Scenario | Response Time |
|-------|----------|---------------|
| 1 | Unprotected site | 0.5-2s |
| 1 | With Tor proxy | 1-3s |
| 2 | JavaScript site | 3-8s |
| 2 | With Tor proxy | 5-10s |
| 3 | Cloudflare challenge | 10-30s |

### Optimization Tips

1. **Use site profiles** for known sites to skip unnecessary layers
2. **Avoid proxy** when not needed (faster)
3. **Force specific layer** if you know site requirements
4. **Batch requests** to amortize Tor circuit rotation cost

## Testing

### Run Test Suite

```bash
python test_scraper.py
```

### Test Coverage

- Challenge detection (Cloudflare, PerimeterX, DataDome, generic)
- Content meaningfulness validation
- Domain extraction and profile matching
- ScrapeResult serialization
- Layer availability checks
- Live scraping test (example.com)

### Manual Testing

```bash
# Test each layer individually
python scraper.py http://example.com --layer 1
python scraper.py http://example.com --layer 2
python scraper.py http://example.com --layer 3

# Test proxy functionality
python scraper.py http://example.com --proxy

# Test full escalation
python scraper.py https://protected-site.com -v
```

## Troubleshooting

### curl_cffi Not Available

```
⚠ curl_cffi not available - Layer 1 will be skipped
```

**Solution**: Install curl_cffi
```bash
pip install curl_cffi>=0.7.0
```

### Tor Connection Failed

```
ERROR: Failed to rotate Tor circuit: Connection refused
```

**Solution**: Ensure Tor is running
```bash
docker compose ps tor-proxy
docker compose logs tor-proxy
```

### Firecrawl API Error

```
ERROR: Firecrawl API error: 404
```

**Solution**: Check Firecrawl service
```bash
docker compose ps firecrawl
curl http://localhost:3002/health
```

### FlareSolverr Timeout

```
ERROR: FlareSolverr API timeout
```

**Solution**: Increase timeout or check service
```bash
docker compose logs flaresolverr
```

### All Layers Failed

If all layers fail:
1. Check if site is accessible in browser
2. Verify all services are running: `docker compose ps`
3. Check service logs: `docker compose logs`
4. Try with verbose logging: `python scraper.py URL -v`
5. Test individual layers: `python scraper.py URL --layer N`

## Integration Examples

### Python Script

```python
from scraper import scrape

# Basic usage
result = scrape("https://example.com")
if result["result"]["success"]:
    content = result["result"]["content"]
    print(f"Scraped {len(content)} bytes")
else:
    print(f"Failed: {result['result']['error']}")

# With options
result = scrape(
    "https://example.com",
    force_layer=2,
    force_proxy=True,
    quiet=True
)
```

### Batch Processing

```python
import json
from pathlib import Path
from scraper import scrape

urls = [
    "https://example.com",
    "https://example.org",
    "https://example.net",
]

results = []
for url in urls:
    print(f"Scraping {url}...")
    result = scrape(url, quiet=True)
    results.append(result)

# Save all results
Path("batch_results.json").write_text(
    json.dumps(results, indent=2)
)
```

### API Wrapper

```python
from flask import Flask, jsonify, request
from scraper import scrape

app = Flask(__name__)

@app.route('/scrape', methods=['POST'])
def api_scrape():
    data = request.json
    url = data.get('url')

    if not url:
        return jsonify({"error": "URL required"}), 400

    result = scrape(
        url,
        force_layer=data.get('layer'),
        force_proxy=data.get('use_proxy'),
        quiet=True
    )

    return jsonify(result)

if __name__ == '__main__':
    app.run(port=5000)
```

## Best Practices

1. **Start simple**: Let the scraper escalate automatically
2. **Use site profiles**: Add profiles for frequently scraped domains
3. **Monitor performance**: Track which layers succeed for optimization
4. **Handle failures gracefully**: Check `success` flag before processing content
5. **Respect rate limits**: Add delays between requests to same domain
6. **Cache results**: Store successful scrapes to avoid redundant requests
7. **Rotate proxies**: Consider multiple Tor circuits or proxy providers for scale

## Security Notes

- **Tor anonymity**: Provides IP rotation, not guaranteed anonymity
- **Challenge solving**: FlareSolverr may violate site terms of service
- **Rate limiting**: Implement your own rate limiting for production use
- **User agents**: Scraper uses realistic headers but may still be detectable
- **Legal compliance**: Ensure scraping complies with site terms and local laws

## Performance Tuning

### For Speed

```python
# Force fastest layer
scrape(url, force_layer=1, force_proxy=False)

# Use site profiles to skip unnecessary layers
# Add to SITE_PROFILES in scraper.py
```

### For Success Rate

```python
# Use full escalation with proxy
scrape(url, force_proxy=True)

# Start at browser layer for JS-heavy sites
scrape(url, force_layer=2)
```

### For Scale

- Use multiple Tor circuits (separate Docker containers)
- Implement connection pooling for curl_cffi
- Cache Firecrawl sessions
- Distribute across multiple FlareSolverr instances

## License

See main project LICENSE file.

## Support

For issues or questions:
1. Check troubleshooting section above
2. Review service logs: `docker compose logs`
3. Run test suite: `python test_scraper.py`
4. Enable verbose logging: `-v` flag

## Credits

Built with:
- [curl_cffi](https://github.com/yifeikong/curl-cffi) - TLS fingerprinting
- [Firecrawl](https://github.com/mendableai/firecrawl) - Browser automation
- [FlareSolverr](https://github.com/FlareSolverr/FlareSolverr) - Challenge solving
- [Tor](https://www.torproject.org/) - Proxy/anonymization
