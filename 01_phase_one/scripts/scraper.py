#!/usr/bin/env python3
"""
Production-ready web scraper with 3-layer escalation strategy.

Layer 1: curl_cffi - Fast TLS fingerprinting without JS rendering
Layer 2: Firecrawl API - Full browser with JavaScript execution
Layer 3: FlareSolverr - Dedicated Cloudflare/anti-bot challenge solver

Author: Claude Code (Python Pro Agent)
"""

import argparse
import json
import logging
import os
import re
import socket
import sys
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import requests

# Optional curl_cffi import
try:
    from curl_cffi import requests as curl_requests
    CURL_CFFI_AVAILABLE = True
except ImportError:
    CURL_CFFI_AVAILABLE = False
    logging.warning("curl_cffi not available - Layer 1 will be skipped")


# ============================================================================
# Configuration
# ============================================================================

TOR_CONTROL_PORT = int(os.getenv("TOR_CONTROL_PORT", "9051"))
TOR_CONTROL_PASSWORD = os.getenv("TOR_CONTROL_PASSWORD", "")
TOR_PROXY_URL = os.getenv("TOR_PROXY_URL", "http://localhost:8118")
FIRECRAWL_API_URL = os.getenv("FIRECRAWL_API_URL", "http://localhost:3002/v1/scrape")
FLARESOLVERR_API_URL = os.getenv("FLARESOLVERR_API_URL", "http://localhost:8191/v1")

# Site-specific optimization profiles
SITE_PROFILES = {
    "zillow.com": {"start_layer": 2, "use_proxy": True, "human_behavior": True},
    "redfin.com": {"start_layer": 2, "use_proxy": True, "human_behavior": True},
    "realtor.com": {"start_layer": 2, "use_proxy": True, "human_behavior": True},
    "example.com": {"start_layer": 1, "use_proxy": False, "human_behavior": False},
}

# Detection patterns for challenge pages
CHALLENGE_PATTERNS = {
    "cloudflare": [
        "cf-browser-verification",
        "Just a moment...",
        "Checking your browser",
        "ray ID:",
        "cf-challenge",
        "__cf_chl_jschl_tk__",
    ],
    "perimeterx": [
        "px-captcha",
        "_px",
        "perimeterx",
        "pxCaptcha",
    ],
    "datadome": [
        "datadome",
        "dd_challenge",
        "geo.captcha-delivery.com",
    ],
    "generic": [
        "Access denied",
        "bot detection",
        "Attention Required",
        "Access Denied",
        "Forbidden",
        "Please verify you are human",
    ],
}


# ============================================================================
# Data Models
# ============================================================================

@dataclass
class ScrapeResult:
    """Result of a scraping attempt."""
    success: bool
    content: Optional[str] = None
    method: Optional[str] = None
    status_code: Optional[int] = None
    error: Optional[str] = None
    elapsed: float = 0.0
    challenge_detected: bool = False

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)


# ============================================================================
# Core Utilities (Subtask 4.1)
# ============================================================================

def is_challenge_page(html: str) -> tuple[bool, Optional[str]]:
    """
    Detect if page is a bot challenge or blocking page.

    Args:
        html: HTML content to analyze

    Returns:
        Tuple of (is_challenge, challenge_type)
    """
    if not html or len(html) < 100:
        return False, None

    html_lower = html.lower()

    # Check each challenge type
    for challenge_type, patterns in CHALLENGE_PATTERNS.items():
        for pattern in patterns:
            if pattern.lower() in html_lower:
                logging.debug(f"Challenge detected: {challenge_type} (pattern: {pattern})")
                return True, challenge_type

    return False, None


def is_content_meaningful(html: str, min_length: int = 500) -> bool:
    """
    Check if HTML content is meaningful (not just boilerplate).

    Args:
        html: HTML content to analyze
        min_length: Minimum text length after stripping HTML tags

    Returns:
        True if content appears meaningful
    """
    if not html:
        return False

    # Strip HTML tags and whitespace
    text = re.sub(r'<[^>]+>', '', html)
    text = re.sub(r'\s+', ' ', text).strip()

    # Check if we have enough actual text content
    return len(text) >= min_length


def rotate_tor_circuit() -> bool:
    """
    Send NEWNYM signal to Tor control port to rotate circuit.

    Returns:
        True if successful, False otherwise
    """
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(10)  # 10 second timeout
            sock.connect(("127.0.0.1", TOR_CONTROL_PORT))

            # Authenticate if password is set
            if TOR_CONTROL_PASSWORD:
                sock.send(f'AUTHENTICATE "{TOR_CONTROL_PASSWORD}"\r\n'.encode())
                response = sock.recv(1024).decode()
                if "250 OK" not in response:
                    logging.error(f"Tor authentication failed: {response}")
                    return False
            else:
                sock.send(b'AUTHENTICATE ""\r\n')
                response = sock.recv(1024).decode()
                if "250 OK" not in response:
                    logging.error(f"Tor authentication failed: {response}")
                    return False

            # Send NEWNYM signal
            sock.send(b"SIGNAL NEWNYM\r\n")
            response = sock.recv(1024).decode()

            if "250 OK" in response:
                logging.info("Tor circuit rotated successfully")
                time.sleep(2)  # Wait for new circuit
                return True
            else:
                logging.error(f"Tor NEWNYM failed: {response}")
                return False

    except Exception as e:
        logging.error(f"Failed to rotate Tor circuit: {e}")
        return False


def extract_domain(url: str) -> str:
    """Extract domain from URL for profile matching."""
    match = re.search(r'https?://([^/]+)', url)
    if match:
        domain = match.group(1)
        # Remove www. prefix
        domain = re.sub(r'^www\.', '', domain)
        return domain
    return ""


def get_site_profile(url: str) -> dict:
    """Get site-specific configuration profile."""
    domain = extract_domain(url)

    # Check for exact domain match
    for profile_domain, profile in SITE_PROFILES.items():
        if profile_domain in domain:
            logging.info(f"Using profile for {profile_domain}")
            return profile

    # Default profile
    return {"start_layer": 1, "use_proxy": False, "human_behavior": True}


# ============================================================================
# Layer 1: curl_cffi (Subtask 4.2)
# ============================================================================

def try_curl_cffi(url: str, use_proxy: bool = False) -> ScrapeResult:
    """
    Attempt to scrape using curl_cffi with Chrome TLS fingerprint.

    This is the fastest layer - no JavaScript rendering, just HTTP with
    realistic browser fingerprinting.

    Args:
        url: URL to scrape
        use_proxy: Whether to route through Tor proxy

    Returns:
        ScrapeResult with attempt outcome
    """
    if not CURL_CFFI_AVAILABLE:
        return ScrapeResult(
            success=False,
            error="curl_cffi not available",
            method="curl_cffi"
        )

    start_time = time.time()

    try:
        # Realistic browser headers
        headers = {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "DNT": "1",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-User": "?1",
            "Cache-Control": "max-age=0",
        }

        proxies = {"http": TOR_PROXY_URL, "https": TOR_PROXY_URL} if use_proxy else None

        # Use chrome131 impersonation for realistic TLS fingerprint
        response = curl_requests.get(
            url,
            headers=headers,
            impersonate="chrome131",
            proxies=proxies,
            timeout=30,
            allow_redirects=True,
        )

        elapsed = time.time() - start_time

        # Check for challenge pages
        is_challenge, challenge_type = is_challenge_page(response.text)

        if is_challenge:
            return ScrapeResult(
                success=False,
                content=None,
                method="curl_cffi",
                status_code=response.status_code,
                error=f"Challenge page detected: {challenge_type}",
                elapsed=elapsed,
                challenge_detected=True,
            )

        # Check if content is meaningful
        if not is_content_meaningful(response.text):
            return ScrapeResult(
                success=False,
                content=response.text,
                method="curl_cffi",
                status_code=response.status_code,
                error="Content appears to be blocked or empty",
                elapsed=elapsed,
            )

        return ScrapeResult(
            success=True,
            content=response.text,
            method="curl_cffi",
            status_code=response.status_code,
            elapsed=elapsed,
        )

    except Exception as e:
        elapsed = time.time() - start_time
        return ScrapeResult(
            success=False,
            error=f"curl_cffi error: {str(e)}",
            method="curl_cffi",
            elapsed=elapsed,
        )


# ============================================================================
# Layer 2: Firecrawl API (Subtask 4.3)
# ============================================================================

def try_firecrawl(
    url: str,
    use_proxy: bool = False,
    human_behavior: bool = True
) -> ScrapeResult:
    """
    Attempt to scrape using Firecrawl API with full browser rendering.

    This layer handles JavaScript-heavy sites by using a real browser
    instance via the Firecrawl API.

    Args:
        url: URL to scrape
        use_proxy: Whether to route through Tor proxy
        human_behavior: Whether to simulate human browsing patterns

    Returns:
        ScrapeResult with attempt outcome
    """
    start_time = time.time()

    try:
        payload = {
            "url": url,
            "formats": ["markdown", "html"],
            "timeout": 60000,
            "waitFor": 3000,
        }

        # Add proxy configuration if requested
        if use_proxy:
            payload["proxy"] = "http://tor-proxy:8118"

        # Add human behavior simulation if requested
        if human_behavior:
            payload["humanBehavior"] = True

        response = requests.post(
            FIRECRAWL_API_URL,
            json=payload,
            timeout=70,  # Slightly longer than API timeout
        )

        elapsed = time.time() - start_time

        if response.status_code != 200:
            return ScrapeResult(
                success=False,
                error=f"Firecrawl API error: {response.status_code} - {response.text}",
                method="firecrawl",
                status_code=response.status_code,
                elapsed=elapsed,
            )

        data = response.json()

        # Check if scrape was successful
        if not data.get("success", False):
            return ScrapeResult(
                success=False,
                error=f"Firecrawl scrape failed: {data.get('error', 'Unknown error')}",
                method="firecrawl",
                elapsed=elapsed,
            )

        # Extract content (prefer HTML, fallback to markdown)
        content = data.get("data", {}).get("html") or data.get("data", {}).get("markdown")

        if not content:
            return ScrapeResult(
                success=False,
                error="Firecrawl returned no content",
                method="firecrawl",
                elapsed=elapsed,
            )

        # Check for challenge pages
        is_challenge, challenge_type = is_challenge_page(content)

        if is_challenge:
            return ScrapeResult(
                success=False,
                content=None,
                method="firecrawl",
                error=f"Challenge page detected: {challenge_type}",
                elapsed=elapsed,
                challenge_detected=True,
            )

        # Check if content is meaningful
        if not is_content_meaningful(content):
            return ScrapeResult(
                success=False,
                content=content,
                method="firecrawl",
                error="Content appears to be blocked or empty",
                elapsed=elapsed,
            )

        return ScrapeResult(
            success=True,
            content=content,
            method="firecrawl",
            status_code=200,
            elapsed=elapsed,
        )

    except requests.exceptions.Timeout:
        elapsed = time.time() - start_time
        return ScrapeResult(
            success=False,
            error="Firecrawl API timeout",
            method="firecrawl",
            elapsed=elapsed,
        )
    except Exception as e:
        elapsed = time.time() - start_time
        return ScrapeResult(
            success=False,
            error=f"Firecrawl error: {str(e)}",
            method="firecrawl",
            elapsed=elapsed,
        )


# ============================================================================
# Layer 3: FlareSolverr (Subtask 5.1)
# ============================================================================

def try_flaresolverr(url: str) -> ScrapeResult:
    """
    Attempt to scrape using FlareSolverr for Cloudflare challenges.

    This is the last resort layer for sites with active Cloudflare
    JavaScript challenges.

    Args:
        url: URL to scrape

    Returns:
        ScrapeResult with attempt outcome
    """
    start_time = time.time()

    try:
        payload = {
            "cmd": "request.get",
            "url": url,
            "maxTimeout": 60000,
        }

        response = requests.post(
            FLARESOLVERR_API_URL,
            json=payload,
            timeout=70,
        )

        elapsed = time.time() - start_time

        if response.status_code != 200:
            return ScrapeResult(
                success=False,
                error=f"FlareSolverr API error: {response.status_code} - {response.text}",
                method="flaresolverr",
                status_code=response.status_code,
                elapsed=elapsed,
            )

        data = response.json()

        # Check if solution was successful
        if data.get("status") != "ok":
            return ScrapeResult(
                success=False,
                error=f"FlareSolverr failed: {data.get('message', 'Unknown error')}",
                method="flaresolverr",
                elapsed=elapsed,
            )

        # Extract solution HTML
        solution = data.get("solution", {})
        content = solution.get("response")
        status_code = solution.get("status")

        if not content:
            return ScrapeResult(
                success=False,
                error="FlareSolverr returned no content",
                method="flaresolverr",
                elapsed=elapsed,
            )

        # Check if content is meaningful
        if not is_content_meaningful(content):
            return ScrapeResult(
                success=False,
                content=content,
                method="flaresolverr",
                status_code=status_code,
                error="Content appears to be blocked or empty",
                elapsed=elapsed,
            )

        return ScrapeResult(
            success=True,
            content=content,
            method="flaresolverr",
            status_code=status_code,
            elapsed=elapsed,
        )

    except requests.exceptions.Timeout:
        elapsed = time.time() - start_time
        return ScrapeResult(
            success=False,
            error="FlareSolverr API timeout",
            method="flaresolverr",
            elapsed=elapsed,
        )
    except Exception as e:
        elapsed = time.time() - start_time
        return ScrapeResult(
            success=False,
            error=f"FlareSolverr error: {str(e)}",
            method="flaresolverr",
            elapsed=elapsed,
        )


# ============================================================================
# Smart Orchestrator (Subtask 5.2)
# ============================================================================

def scrape(
    url: str,
    force_layer: Optional[int] = None,
    force_proxy: Optional[bool] = None,
    quiet: bool = False
) -> dict:
    """
    Main orchestrator with intelligent 3-layer escalation strategy.

    Escalation Strategy:
    1. curl_cffi without proxy (fastest for unprotected sites)
    2. curl_cffi with Tor proxy (different IP)
    3. Firecrawl without proxy (full browser)
    4. Rotate Tor + Firecrawl with proxy
    5. FlareSolverr (dedicated Cloudflare solver)

    Args:
        url: URL to scrape
        force_layer: Force specific layer (1-3), skip escalation
        force_proxy: Force proxy on/off, override profile
        quiet: Suppress progress logging

    Returns:
        Dictionary with scrape results and metadata
    """
    if not quiet:
        logging.info(f"Starting scrape for: {url}")

    # Get site-specific profile
    profile = get_site_profile(url)
    start_layer = profile.get("start_layer", 1)
    use_proxy = profile.get("use_proxy", False) if force_proxy is None else force_proxy
    human_behavior = profile.get("human_behavior", True)

    attempts = []
    total_start = time.time()

    # Force specific layer if requested
    if force_layer:
        if not quiet:
            logging.info(f"Forcing layer {force_layer}")

        if force_layer == 1:
            result = try_curl_cffi(url, use_proxy=use_proxy)
        elif force_layer == 2:
            result = try_firecrawl(url, use_proxy=use_proxy, human_behavior=human_behavior)
        elif force_layer == 3:
            result = try_flaresolverr(url)
        else:
            raise ValueError(f"Invalid layer: {force_layer} (must be 1-3)")

        attempts.append(result.to_dict())

        return {
            "url": url,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "result": result.to_dict(),
            "total_elapsed": time.time() - total_start,
            "attempts": attempts,
        }

    # ========================================================================
    # Layer 1: curl_cffi without proxy
    # ========================================================================
    if start_layer <= 1 and CURL_CFFI_AVAILABLE:
        if not quiet:
            logging.info("Attempt 1: curl_cffi without proxy")

        result = try_curl_cffi(url, use_proxy=False)
        attempts.append(result.to_dict())

        if result.success:
            if not quiet:
                logging.info(f"Success with curl_cffi (no proxy) in {result.elapsed:.2f}s")
            return {
                "url": url,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "result": result.to_dict(),
                "total_elapsed": time.time() - total_start,
                "attempts": attempts,
            }

        if not quiet:
            logging.warning(f"curl_cffi (no proxy) failed: {result.error}")

    # ========================================================================
    # Layer 2: curl_cffi with Tor proxy
    # ========================================================================
    if start_layer <= 1 and CURL_CFFI_AVAILABLE and (use_proxy or result.challenge_detected):
        if not quiet:
            logging.info("Attempt 2: curl_cffi with Tor proxy")

        result = try_curl_cffi(url, use_proxy=True)
        attempts.append(result.to_dict())

        if result.success:
            if not quiet:
                logging.info(f"Success with curl_cffi (Tor) in {result.elapsed:.2f}s")
            return {
                "url": url,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "result": result.to_dict(),
                "total_elapsed": time.time() - total_start,
                "attempts": attempts,
            }

        if not quiet:
            logging.warning(f"curl_cffi (Tor) failed: {result.error}")

    # ========================================================================
    # Layer 3: Firecrawl without proxy
    # ========================================================================
    if start_layer <= 2:
        if not quiet:
            logging.info("Attempt 3: Firecrawl without proxy")

        result = try_firecrawl(url, use_proxy=False, human_behavior=human_behavior)
        attempts.append(result.to_dict())

        if result.success:
            if not quiet:
                logging.info(f"Success with Firecrawl (no proxy) in {result.elapsed:.2f}s")
            return {
                "url": url,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "result": result.to_dict(),
                "total_elapsed": time.time() - total_start,
                "attempts": attempts,
            }

        if not quiet:
            logging.warning(f"Firecrawl (no proxy) failed: {result.error}")

    # ========================================================================
    # Layer 4: Rotate Tor + Firecrawl with proxy
    # ========================================================================
    if use_proxy or result.challenge_detected:
        if not quiet:
            logging.info("Attempt 4: Rotating Tor circuit and trying Firecrawl with proxy")

        rotate_tor_circuit()

        result = try_firecrawl(url, use_proxy=True, human_behavior=human_behavior)
        attempts.append(result.to_dict())

        if result.success:
            if not quiet:
                logging.info(f"Success with Firecrawl (Tor) in {result.elapsed:.2f}s")
            return {
                "url": url,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "result": result.to_dict(),
                "total_elapsed": time.time() - total_start,
                "attempts": attempts,
            }

        if not quiet:
            logging.warning(f"Firecrawl (Tor) failed: {result.error}")

    # ========================================================================
    # Layer 5: FlareSolverr (last resort)
    # ========================================================================
    if not quiet:
        logging.info("Attempt 5: FlareSolverr (last resort)")

    result = try_flaresolverr(url)
    attempts.append(result.to_dict())

    if result.success:
        if not quiet:
            logging.info(f"Success with FlareSolverr in {result.elapsed:.2f}s")
        return {
            "url": url,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "result": result.to_dict(),
            "total_elapsed": time.time() - total_start,
            "attempts": attempts,
        }

    # ========================================================================
    # All layers failed
    # ========================================================================
    if not quiet:
        logging.error("All scraping layers failed")

    return {
        "url": url,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "result": result.to_dict(),
        "total_elapsed": time.time() - total_start,
        "attempts": attempts,
    }


# ============================================================================
# CLI Interface
# ============================================================================

def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Production web scraper with 3-layer escalation strategy",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Simple scrape
  python scraper.py https://example.com

  # Save to file
  python scraper.py https://example.com -o output.json

  # Force specific layer
  python scraper.py https://example.com --layer 2

  # Force proxy usage
  python scraper.py https://example.com --proxy

  # Quiet mode
  python scraper.py https://example.com -q
        """
    )

    parser.add_argument(
        "url",
        help="URL to scrape"
    )

    parser.add_argument(
        "-o", "--output",
        help="Output file path (JSON format)",
        type=str,
    )

    parser.add_argument(
        "-q", "--quiet",
        help="Suppress progress messages",
        action="store_true",
    )

    parser.add_argument(
        "--layer",
        help="Force specific layer (1=curl_cffi, 2=firecrawl, 3=flaresolverr)",
        type=int,
        choices=[1, 2, 3],
    )

    parser.add_argument(
        "--proxy",
        help="Force proxy usage",
        action="store_true",
        dest="use_proxy",
    )

    parser.add_argument(
        "--no-proxy",
        help="Force no proxy usage",
        action="store_false",
        dest="use_proxy",
    )

    parser.set_defaults(use_proxy=None)

    parser.add_argument(
        "-v", "--verbose",
        help="Enable verbose logging",
        action="store_true",
    )

    args = parser.parse_args()

    # Configure logging
    log_level = logging.DEBUG if args.verbose else (logging.ERROR if args.quiet else logging.INFO)
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Run scraper
    result = scrape(
        url=args.url,
        force_layer=args.layer,
        force_proxy=args.use_proxy,
        quiet=args.quiet,
    )

    # Output results
    if args.output:
        output_path = Path(args.output)
        output_path.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
        if not args.quiet:
            print(f"\nResults saved to: {output_path.absolute()}")
    else:
        print(json.dumps(result, indent=2, ensure_ascii=False))

    # Exit with appropriate code
    sys.exit(0 if result["result"]["success"] else 1)


if __name__ == "__main__":
    main()
