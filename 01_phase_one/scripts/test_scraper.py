#!/usr/bin/env python3
"""
Test suite for scraper.py - validates all layers and utilities.

Run with: python test_scraper.py
"""

import json
import sys
from pathlib import Path

# Import scraper modules
import scraper


def test_challenge_detection():
    """Test challenge page detection."""
    print("\n=== Testing Challenge Detection ===")

    # Cloudflare challenge
    cloudflare_html = """
    <html>
    <head><title>Just a moment...</title></head>
    <body>
    <div id="cf-browser-verification">Checking your browser...</div>
    </body>
    </html>
    """
    is_challenge, challenge_type = scraper.is_challenge_page(cloudflare_html)
    assert is_challenge, "Should detect Cloudflare challenge"
    assert challenge_type == "cloudflare", f"Wrong type: {challenge_type}"
    print("✓ Cloudflare challenge detected")

    # PerimeterX challenge
    perimeterx_html = """
    <html><head><title>Access Check</title></head>
    <body><div class="px-captcha">Please verify you are human</div></body>
    </html>
    """
    is_challenge, challenge_type = scraper.is_challenge_page(perimeterx_html)
    assert is_challenge, "Should detect PerimeterX challenge"
    assert challenge_type == "perimeterx", f"Wrong type: {challenge_type}"
    print("✓ PerimeterX challenge detected")

    # DataDome challenge
    datadome_html = """
    <html><head><title>Access Check</title></head>
    <body><script src="datadome.co/captcha"></script></body>
    </html>
    """
    is_challenge, challenge_type = scraper.is_challenge_page(datadome_html)
    assert is_challenge, "Should detect DataDome challenge"
    assert challenge_type == "datadome", f"Wrong type: {challenge_type}"
    print("✓ DataDome challenge detected")

    # Generic block
    generic_html = """
    <html><head><title>Access Denied</title></head>
    <body><h1>Access Denied</h1><p>Bot detection enabled</p></body>
    </html>
    """
    is_challenge, challenge_type = scraper.is_challenge_page(generic_html)
    assert is_challenge, "Should detect generic block"
    assert challenge_type == "generic", f"Wrong type: {challenge_type}"
    print("✓ Generic block detected")

    # Normal page
    normal_html = "<html><body><h1>Welcome</h1><p>This is a normal page with lots of content.</p></body></html>"
    is_challenge, challenge_type = scraper.is_challenge_page(normal_html)
    assert not is_challenge, "Should not detect challenge on normal page"
    print("✓ Normal page not flagged")


def test_content_meaningful():
    """Test meaningful content detection."""
    print("\n=== Testing Content Meaningfulness ===")

    # Meaningful content
    good_html = "<html><body>" + "<p>Content paragraph.</p>" * 100 + "</body></html>"
    assert scraper.is_content_meaningful(good_html), "Should detect meaningful content"
    print("✓ Meaningful content detected")

    # Empty content
    empty_html = "<html><body></body></html>"
    assert not scraper.is_content_meaningful(empty_html), "Should reject empty content"
    print("✓ Empty content rejected")

    # Short content
    short_html = "<html><body><p>Short</p></body></html>"
    assert not scraper.is_content_meaningful(short_html), "Should reject short content"
    print("✓ Short content rejected")

    # Just boilerplate
    boilerplate_html = "<html><head><script src='x.js'></script></head><body></body></html>"
    assert not scraper.is_content_meaningful(boilerplate_html), "Should reject boilerplate"
    print("✓ Boilerplate rejected")


def test_domain_extraction():
    """Test domain extraction from URLs."""
    print("\n=== Testing Domain Extraction ===")

    test_cases = [
        ("https://www.zillow.com/homes/", "zillow.com"),
        ("http://example.com/path", "example.com"),
        ("https://subdomain.example.com/", "subdomain.example.com"),
        ("https://www.example.com/", "example.com"),
    ]

    for url, expected in test_cases:
        domain = scraper.extract_domain(url)
        assert domain == expected, f"Expected {expected}, got {domain}"
        print(f"✓ {url} -> {domain}")


def test_site_profiles():
    """Test site profile matching."""
    print("\n=== Testing Site Profiles ===")

    # Known profile
    profile = scraper.get_site_profile("https://www.zillow.com/homes/")
    assert profile["start_layer"] == 2, "Zillow should start at layer 2"
    assert profile["use_proxy"] == True, "Zillow should use proxy"
    print("✓ Zillow profile matched")

    # Unknown domain (default profile)
    profile = scraper.get_site_profile("https://unknown-site.com/")
    assert profile["start_layer"] == 1, "Unknown site should start at layer 1"
    assert profile["use_proxy"] == False, "Unknown site should not use proxy by default"
    print("✓ Default profile used for unknown site")


def test_scrape_result_serialization():
    """Test ScrapeResult dataclass serialization."""
    print("\n=== Testing ScrapeResult Serialization ===")

    result = scraper.ScrapeResult(
        success=True,
        content="<html>test</html>",
        method="curl_cffi",
        status_code=200,
        elapsed=1.23,
    )

    result_dict = result.to_dict()
    assert result_dict["success"] == True
    assert result_dict["method"] == "curl_cffi"
    assert result_dict["status_code"] == 200
    print("✓ ScrapeResult serialization works")

    # Test JSON serialization
    json_str = json.dumps(result_dict)
    assert len(json_str) > 0
    print("✓ JSON serialization works")


def test_layer_availability():
    """Test which layers are available."""
    print("\n=== Testing Layer Availability ===")

    if scraper.CURL_CFFI_AVAILABLE:
        print("✓ curl_cffi available (Layer 1)")
    else:
        print("⚠ curl_cffi not available (Layer 1 will be skipped)")

    # Check if Firecrawl API is accessible
    try:
        import requests
        response = requests.get("http://localhost:3002/health", timeout=2)
        print("✓ Firecrawl API accessible (Layer 2)")
    except Exception:
        print("⚠ Firecrawl API not accessible (Layer 2 will fail)")

    # Check if FlareSolverr is accessible
    try:
        response = requests.get("http://localhost:8191", timeout=2)
        print("✓ FlareSolverr accessible (Layer 3)")
    except Exception:
        print("⚠ FlareSolverr not accessible (Layer 3 will fail)")


def test_live_scrape():
    """Test live scraping with example.com."""
    print("\n=== Testing Live Scrape (example.com) ===")

    try:
        result = scraper.scrape(
            "http://example.com",
            quiet=True,
        )

        print(f"Success: {result['result']['success']}")
        print(f"Method: {result['result']['method']}")
        print(f"Elapsed: {result['total_elapsed']:.2f}s")
        print(f"Attempts: {len(result['attempts'])}")

        if result['result']['success']:
            content_preview = result['result']['content'][:100] if result['result']['content'] else "None"
            print(f"Content preview: {content_preview}...")
            print("✓ Live scrape successful")
        else:
            print(f"✗ Live scrape failed: {result['result']['error']}")

    except Exception as e:
        print(f"✗ Live scrape error: {e}")


def run_all_tests():
    """Run all test functions."""
    print("=" * 70)
    print("SCRAPER TEST SUITE")
    print("=" * 70)

    test_functions = [
        test_challenge_detection,
        test_content_meaningful,
        test_domain_extraction,
        test_site_profiles,
        test_scrape_result_serialization,
        test_layer_availability,
        test_live_scrape,
    ]

    passed = 0
    failed = 0

    for test_func in test_functions:
        try:
            test_func()
            passed += 1
        except AssertionError as e:
            print(f"\n✗ FAILED: {test_func.__name__}")
            print(f"  Error: {e}")
            failed += 1
        except Exception as e:
            print(f"\n✗ ERROR in {test_func.__name__}: {e}")
            failed += 1

    print("\n" + "=" * 70)
    print(f"RESULTS: {passed} passed, {failed} failed")
    print("=" * 70)

    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
