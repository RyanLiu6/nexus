#!/usr/bin/env python3
"""Prometheus exporter for Tailscale API key expiration.

Queries the Tailscale API to get API key information and exposes
the expiration time as a Prometheus metric.
"""

import logging
import os
import time
from datetime import datetime
from typing import Optional

import requests
from prometheus_client import Gauge, Info, start_http_server

TAILSCALE_API_KEY = os.environ.get("TAILSCALE_API_KEY", "")
TAILNET_NAME = os.environ.get("TAILNET_NAME", "")
SCRAPE_INTERVAL = int(os.environ.get("SCRAPE_INTERVAL", "3600"))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

api_key_expiry_seconds = Gauge(
    "tailscale_api_key_expiry_seconds",
    "Seconds until the Tailscale API key expires",
)

api_key_expiry_timestamp = Gauge(
    "tailscale_api_key_expiry_timestamp",
    "Unix timestamp when the Tailscale API key expires",
)

api_key_info = Info(
    "tailscale_api_key",
    "Information about the Tailscale API key",
)


def get_api_key_expiry() -> Optional[datetime]:
    """Query the Tailscale API to get the current key's expiration.

    Returns:
        The expiration datetime if available, None otherwise.
    """
    if not TAILSCALE_API_KEY or not TAILNET_NAME:
        logger.warning("TAILSCALE_API_KEY or TAILNET_NAME not configured")
        return None

    try:
        # The API key we're using is the one we want to check
        # We can get its info by listing keys and finding the one that matches
        # Or we can use the /api/v2/tailnet/{tailnet}/keys endpoint
        headers = {"Authorization": f"Bearer {TAILSCALE_API_KEY}"}
        url = f"https://api.tailscale.com/api/v2/tailnet/{TAILNET_NAME}/keys"

        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()

        keys = response.json().get("keys", [])

        # Find the key that matches our API key prefix
        # API keys start with "tskey-api-" followed by an ID
        key_prefix = TAILSCALE_API_KEY[:20] if len(TAILSCALE_API_KEY) > 20 else ""

        for key in keys:
            key_id = key.get("id", "")
            if key_prefix and key_id in TAILSCALE_API_KEY:
                expires_str = key.get("expires")
                if expires_str:
                    # Parse ISO 8601 format
                    expires = datetime.fromisoformat(expires_str.replace("Z", "+00:00"))
                    logger.info(f"Found API key {key_id}, expires: {expires}")
                    return expires

        # If we can't find the specific key, check if we got any response
        # which means the key is still valid
        logger.info("API key is valid but couldn't determine exact expiration")
        return None

    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 401:
            logger.error("API key is invalid or expired")
        else:
            logger.error(f"HTTP error querying Tailscale API: {e}")
        return None
    except Exception as e:
        logger.error(f"Error querying Tailscale API: {e}")
        return None


def update_metrics() -> None:
    """Update Prometheus metrics with current API key status."""
    expiry = get_api_key_expiry()

    if expiry:
        now = datetime.now(expiry.tzinfo)
        seconds_until_expiry = (expiry - now).total_seconds()
        expiry_timestamp = expiry.timestamp()

        api_key_expiry_seconds.set(seconds_until_expiry)
        api_key_expiry_timestamp.set(expiry_timestamp)
        api_key_info.info(
            {
                "expires": expiry.isoformat(),
                "tailnet": TAILNET_NAME,
                "status": "valid",
            }
        )

        days_remaining = seconds_until_expiry / 86400
        logger.info(f"API key expires in {days_remaining:.1f} days")
    else:
        # Set to -1 to indicate unknown/error state
        api_key_expiry_seconds.set(-1)
        api_key_expiry_timestamp.set(0)
        api_key_info.info(
            {
                "expires": "unknown",
                "tailnet": TAILNET_NAME,
                "status": "unknown",
            }
        )


def main() -> None:
    """Start the exporter and periodically update metrics."""
    port = int(os.environ.get("PORT", "9199"))

    logger.info(f"Starting Tailscale exporter on port {port}")
    logger.info(f"Tailnet: {TAILNET_NAME}")
    logger.info(f"Scrape interval: {SCRAPE_INTERVAL}s")

    if not TAILSCALE_API_KEY:
        logger.error("TAILSCALE_API_KEY not set")
    if not TAILNET_NAME:
        logger.error("TAILNET_NAME not set")

    start_http_server(port)
    logger.info(f"Metrics available at http://localhost:{port}/metrics")

    while True:
        update_metrics()
        time.sleep(SCRAPE_INTERVAL)


if __name__ == "__main__":
    main()
