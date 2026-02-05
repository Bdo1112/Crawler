#!/usr/bin/env python3
"""
Example usage patterns for the scraper.

This demonstrates various ways to use the scraper module.
"""

import json
from pathlib import Path
from scraper import scrape, ScrapeResult


def example_basic():
    """Basic scraping example."""
    print("\n=== Basic Scrape ===")

    result = scrape("http://example.com")

    if result["result"]["success"]:
        print(f"✓ Success!")
        print(f"  Method: {result['result']['method']}")
        print(f"  Time: {result['total_elapsed']:.2f}s")
        print(f"  Content length: {len(result['result']['content'])} chars")
    else:
        print(f"✗ Failed: {result['result']['error']}")


def example_force_layer():
    """Force specific scraping layer."""
    print("\n=== Force Specific Layer ===")

    # Try with Firecrawl (layer 2)
    result = scrape(
        "http://example.com",
        force_layer=2,
        quiet=True
    )

    print(f"Method used: {result['result']['method']}")
    print(f"Success: {result['result']['success']}")


def example_with_proxy():
    """Scrape with forced proxy usage."""
    print("\n=== Scrape with Proxy ===")

    result = scrape(
        "http://example.com",
        force_proxy=True,
        quiet=True
    )

    print(f"Success: {result['result']['success']}")
    print(f"Attempts: {len(result['attempts'])}")


def example_batch_scraping():
    """Batch scrape multiple URLs."""
    print("\n=== Batch Scraping ===")

    urls = [
        "http://example.com",
        "http://example.org",
        "http://example.net",
    ]

    results = []
    for i, url in enumerate(urls, 1):
        print(f"Scraping {i}/{len(urls)}: {url}")
        result = scrape(url, quiet=True)
        results.append(result)

        status = "✓" if result["result"]["success"] else "✗"
        print(f"  {status} {result['result']['method']} - {result['total_elapsed']:.2f}s")

    # Save all results
    output_file = Path("batch_results.json")
    output_file.write_text(json.dumps(results, indent=2))
    print(f"\nResults saved to: {output_file.absolute()}")


def example_error_handling():
    """Demonstrate error handling."""
    print("\n=== Error Handling ===")

    result = scrape("http://invalid-url-that-does-not-exist.com", quiet=True)

    if not result["result"]["success"]:
        print("Scrape failed as expected")
        print(f"Error: {result['result']['error']}")
        print(f"Attempted {len(result['attempts'])} layers")

        # Show each attempt
        for i, attempt in enumerate(result['attempts'], 1):
            print(f"  Attempt {i}: {attempt['method']} - {attempt['error']}")


def example_content_extraction():
    """Extract and process scraped content."""
    print("\n=== Content Extraction ===")

    result = scrape("http://example.com", quiet=True)

    if result["result"]["success"]:
        content = result["result"]["content"]

        # Simple extraction examples
        print(f"Content length: {len(content)}")
        print(f"Has <title>: {'<title>' in content}")
        print(f"Has <body>: {'<body>' in content}")

        # Extract title
        import re
        title_match = re.search(r'<title>(.*?)</title>', content, re.IGNORECASE)
        if title_match:
            print(f"Title: {title_match.group(1)}")


def example_site_specific():
    """Use site-specific configurations."""
    print("\n=== Site-Specific Config ===")

    # Zillow uses predefined profile (layer 2, proxy)
    print("Scraping Zillow (will use profile)...")
    result = scrape("https://www.zillow.com/homes/", quiet=True)
    print(f"  Started at layer: 2 (Firecrawl)")
    print(f"  Success: {result['result']['success']}")

    # Unknown site uses default profile (layer 1, no proxy)
    print("\nScraping unknown site (will use default)...")
    result = scrape("http://unknown-site.example", quiet=True)
    print(f"  Started at layer: 1 (curl_cffi)")
    print(f"  Success: {result['result']['success']}")


def example_monitoring():
    """Monitor scraping performance."""
    print("\n=== Performance Monitoring ===")

    result = scrape("http://example.com", quiet=True)

    # Performance metrics
    print(f"Total time: {result['total_elapsed']:.2f}s")
    print(f"Attempts: {len(result['attempts'])}")

    # Show timing for each attempt
    print("\nTiming breakdown:")
    for attempt in result['attempts']:
        method = attempt['method']
        elapsed = attempt['elapsed']
        success = "✓" if attempt['success'] else "✗"
        print(f"  {success} {method:15s} {elapsed:6.2f}s")

    # Calculate success rate
    successful = sum(1 for a in result['attempts'] if a['success'])
    success_rate = (successful / len(result['attempts'])) * 100
    print(f"\nSuccess rate: {success_rate:.1f}%")


def main():
    """Run all examples."""
    print("=" * 70)
    print("SCRAPER USAGE EXAMPLES")
    print("=" * 70)

    examples = [
        example_basic,
        example_force_layer,
        example_with_proxy,
        example_batch_scraping,
        example_error_handling,
        example_content_extraction,
        example_site_specific,
        example_monitoring,
    ]

    for example_func in examples:
        try:
            example_func()
        except Exception as e:
            print(f"\n✗ Example failed: {e}")

    print("\n" + "=" * 70)
    print("Examples completed!")
    print("=" * 70)


if __name__ == "__main__":
    main()
