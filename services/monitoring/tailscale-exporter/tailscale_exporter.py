#!/usr/bin/env python3
"""Prometheus exporter for Tailscale API key expiration.

Queries the Tailscale API to get information about all API keys
and exposes their expiration time as Prometheus metrics.
"""

import logging
import os
import time
from datetime import datetime
from typing import Any, cast

import requests
from prometheus_client import Gauge, start_http_server

TAILSCALE_API_KEY = os.environ.get("TAILSCALE_API_KEY", "")
TAILNET_NAME = os.environ.get("TAILNET_NAME", "")
SCRAPE_INTERVAL = int(os.environ.get("SCRAPE_INTERVAL", "3600"))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Metrics
KEY_EXPIRY_TIMESTAMP = Gauge(
    "tailscale_key_expiry_timestamp",
    "Unix timestamp when the Tailscale API key expires",
    ["key_id", "description", "user_login"],
)

KEY_DAYS_REMAINING = Gauge(
    "tailscale_key_days_remaining",
    "Days remaining until the Tailscale API key expires",
    ["key_id", "description", "user_login"],
)


# State to track known keys for cleanup
KNOWN_KEY_LABELS: set[tuple[str, str, str]] = set()


def get_keys() -> list[dict[str, Any]]:
    """Query the Tailscale API to get all keys.

    Returns:
        A list of key dictionaries.
    """
    if not TAILSCALE_API_KEY or not TAILNET_NAME:
        logger.warning("TAILSCALE_API_KEY or TAILNET_NAME not configured")
        return []

    try:
        headers = {"Authorization": f"Bearer {TAILSCALE_API_KEY}"}
        url = f"https://api.tailscale.com/api/v2/tailnet/{TAILNET_NAME}/keys"

        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()

        data = response.json()
        return cast(list[dict[str, Any]], data.get("keys", []))

    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 401:
            logger.error("API key is invalid or expired")
        elif e.response.status_code == 403:
            logger.error("API key does not have permission to list keys")
        else:
            logger.error(f"HTTP error querying Tailscale API: {e}")
        return []
    except Exception as e:
        logger.error(f"Error querying Tailscale API: {e}")
        return []


def update_metrics() -> None:
    """Update Prometheus metrics with current key status."""
    global KNOWN_KEY_LABELS
    keys = get_keys()

    current_labels: set[tuple[str, str, str]] = set()

    for key in keys:
        key_id = key.get("id", "unknown")

        # Skip revoked keys
        if key.get("revoked"):
            continue

        description = key.get("description", "")
        # API doesn't always return user info in the key object directly
        # depending on version, but let's see if we can find relevant metadata.
        user_login = "unknown"

        expires_str = key.get("expires")
        if not expires_str:
            continue

        try:
            # Parse ISO 8601 format: 2026-01-23T12:00:00Z
            expires = datetime.fromisoformat(expires_str.replace("Z", "+00:00"))

            now = datetime.now(expires.tzinfo)
            seconds_remaining = (expires - now).total_seconds()
            days_remaining = seconds_remaining / 86400

            labels = (key_id, description, user_login)

            KEY_EXPIRY_TIMESTAMP.labels(
                key_id=key_id, description=description, user_login=user_login
            ).set(expires.timestamp())

            KEY_DAYS_REMAINING.labels(
                key_id=key_id, description=description, user_login=user_login
            ).set(days_remaining)

            current_labels.add(labels)

            if days_remaining < 7:
                logger.warning(
                    f"Key {key_id} ({description}) expires in {days_remaining:.1f} days"
                )

        except ValueError as e:
            logger.error(f"Error parsing date for key {key_id}: {e}")

    # Remove metrics for keys that are no longer present
    for labels in KNOWN_KEY_LABELS - current_labels:
        key_id, description, user_login = labels
        try:
            KEY_EXPIRY_TIMESTAMP.remove(
                key_id=key_id, description=description, user_login=user_login
            )
            KEY_DAYS_REMAINING.remove(
                key_id=key_id, description=description, user_login=user_login
            )
            logger.info(f"Removed metrics for revoked/deleted key {key_id}")
        except KeyError:
            pass  # Metric already removed or not found

    KNOWN_KEY_LABELS = current_labels
    logger.info(f"Updated metrics for {len(current_labels)} keys")


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

    # Initial update
    update_metrics()

    while True:
        time.sleep(SCRAPE_INTERVAL)
        update_metrics()


if __name__ == "__main__":
    main()
