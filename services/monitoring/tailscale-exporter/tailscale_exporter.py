#!/usr/bin/env python3
"""Prometheus exporter for Tailscale API key expiration.

Queries the Tailscale API to get information about all API keys
and exposes their expiration time as Prometheus metrics.
"""

import logging
import os
import signal
import time
from datetime import datetime
from typing import Any, cast

import requests
from prometheus_client import Gauge, start_http_server

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class TailscaleExporter:
    """Prometheus exporter for Tailscale API key expiration monitoring.

    Queries the Tailscale API periodically and exposes key expiration
    times as Prometheus metrics for alerting on upcoming expirations.

    Attributes:
        api_key: Tailscale API key for authentication.
        tailnet: Tailnet name for API queries (e.g., 'tail1234').
        scrape_interval: Seconds between API queries.
        port: HTTP port for Prometheus metrics endpoint.
        running: Whether the exporter main loop is active.
    """

    def __init__(
        self,
        api_key: str,
        tailnet: str,
        scrape_interval: int = 3600,
        port: int = 9199,
    ) -> None:
        """Initialize the exporter.

        Args:
            api_key: Tailscale API key for authentication.
            tailnet: Tailnet name (e.g., 'tail1234').
            scrape_interval: Seconds between API queries (default: 3600).
            port: HTTP port for Prometheus metrics (default: 9199).
        """
        self.api_key = api_key
        self.tailnet = tailnet
        self.scrape_interval = scrape_interval
        self.port = port
        self.running = True
        self.known_key_labels: set[tuple[str, str]] = set()

        # Metrics
        self.key_expiry_timestamp = Gauge(
            "tailscale_key_expiry_timestamp",
            "Unix timestamp when the Tailscale API key expires",
            ["key_id", "description"],
        )
        self.key_days_remaining = Gauge(
            "tailscale_key_days_remaining",
            "Days remaining until the Tailscale API key expires",
            ["key_id", "description"],
        )
        self.exporter_up = Gauge(
            "tailscale_exporter_up",
            "Whether the Tailscale API query succeeded (1=success, 0=failure)",
        )

    def get_keys(self) -> tuple[list[dict[str, Any]], bool]:
        """Query the Tailscale API to get all keys.

        Returns:
            A tuple of (list of key dictionaries, success status).
        """
        if not self.api_key or not self.tailnet:
            logger.warning("API key or tailnet not configured")
            return [], False

        try:
            headers = {"Authorization": f"Bearer {self.api_key}"}
            url = f"https://api.tailscale.com/api/v2/tailnet/{self.tailnet}/keys"

            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()

            data = response.json()
            return cast(list[dict[str, Any]], data.get("keys", [])), True

        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 401:
                logger.error("API key is invalid or expired")
            elif e.response.status_code == 403:
                logger.error("API key does not have permission to list keys")
            else:
                logger.error(f"HTTP error querying Tailscale API: {e}")
            return [], False
        except requests.exceptions.RequestException as e:
            logger.error(f"Network error querying Tailscale API: {e}")
            return [], False
        except (ValueError, KeyError) as e:
            logger.error(f"Error parsing API response: {e}")
            return [], False

    def update_metrics(self) -> None:
        """Update Prometheus metrics with current key status."""
        keys, success = self.get_keys()
        self.exporter_up.set(1 if success else 0)
        current_labels: set[tuple[str, str]] = set()

        for key in keys:
            key_id = key.get("id", "unknown")

            # Skip revoked keys
            if key.get("revoked"):
                continue

            description = key.get("description", "")

            expires_str = key.get("expires")
            if not expires_str:
                continue

            try:
                # Parse ISO 8601 format: 2026-01-23T12:00:00Z
                expires = datetime.fromisoformat(expires_str.replace("Z", "+00:00"))

                now = datetime.now(expires.tzinfo)
                seconds_remaining = (expires - now).total_seconds()
                days_remaining = seconds_remaining / 86400

                labels = (key_id, description)

                self.key_expiry_timestamp.labels(
                    key_id=key_id, description=description
                ).set(expires.timestamp())

                self.key_days_remaining.labels(
                    key_id=key_id, description=description
                ).set(days_remaining)

                current_labels.add(labels)

                if days_remaining < 7:
                    logger.warning(
                        f"Key {key_id} ({description}) "
                        f"expires in {days_remaining:.1f} days"
                    )

            except ValueError as e:
                logger.error(f"Error parsing date for key {key_id}: {e}")

        # Remove metrics for keys that are no longer present
        for labels in self.known_key_labels - current_labels:
            key_id, description = labels
            try:
                self.key_expiry_timestamp.remove(key_id=key_id, description=description)
                self.key_days_remaining.remove(key_id=key_id, description=description)
                logger.info(f"Removed metrics for revoked/deleted key {key_id}")
            except KeyError:
                pass

        self.known_key_labels = current_labels
        logger.info(f"Updated metrics for {len(current_labels)} keys")

    def handle_shutdown(self, signum: int, frame: Any) -> None:
        """Handle shutdown signals gracefully."""
        logger.info(f"Received signal {signum}, shutting down...")
        self.running = False

    def run(self) -> None:
        """Start the exporter and periodically update metrics."""
        logger.info(f"Starting Tailscale exporter on port {self.port}")
        logger.info(f"Tailnet: {self.tailnet}")
        logger.info(f"Scrape interval: {self.scrape_interval}s")

        if not self.api_key:
            logger.error("TAILSCALE_API_KEY not set")
        if not self.tailnet:
            logger.error("TAILNET_ID not set")

        # Setup signal handlers
        signal.signal(signal.SIGTERM, self.handle_shutdown)
        signal.signal(signal.SIGINT, self.handle_shutdown)

        # Start HTTP server
        start_http_server(self.port)
        logger.info(f"Metrics available at http://localhost:{self.port}/metrics")

        # Initial update
        self.update_metrics()
        last_update = time.time()

        # Main loop
        while self.running:
            time.sleep(1)
            if time.time() - last_update >= self.scrape_interval:
                self.update_metrics()
                last_update = time.time()

        logger.info("Exporter stopped")


def main() -> None:
    """Entry point for the exporter."""
    api_key = os.environ.get("TAILSCALE_API_KEY", "")
    tailnet = os.environ.get("TAILNET_ID", "")
    scrape_interval = int(os.environ.get("SCRAPE_INTERVAL", "3600"))
    port = int(os.environ.get("PORT", "9199"))

    exporter = TailscaleExporter(
        api_key=api_key,
        tailnet=tailnet,
        scrape_interval=scrape_interval,
        port=port,
    )
    exporter.run()


if __name__ == "__main__":
    main()
