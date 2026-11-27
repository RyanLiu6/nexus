#!/usr/bin/env python3
"""Sync Discord webhook URL from Nexus secrets to Beszel and Uptime Kuma.

Idempotently updates the Discord notification webhook in both Beszel
(PocketBase API) and Uptime Kuma (Socket.IO API via docker exec) so that
rotating `discord_webhook_url` in `config/secrets.enc.yml` propagates
automatically on deploy.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

import yaml

NEXUS_ROOT = Path(__file__).resolve().parent.parent
ENV_FILE = NEXUS_ROOT / ".env"
SECRETS_FILE = NEXUS_ROOT / "config" / "secrets.enc.yml"


def load_config() -> dict[str, str]:
    """Load config from environment, .env, and SOPS secrets as fallback."""
    cfg: dict[str, str] = {}

    if ENV_FILE.exists():
        for line in ENV_FILE.read_text().splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            cfg[k.strip()] = v.strip().strip('"').strip("'")

    # Overlay process environment
    for key in (
        "NEXUS_DOMAIN",
        "DISCORD_WEBHOOK_URL",
        "BESZEL_ADMIN_EMAIL",
        "BESZEL_ADMIN_PASSWORD",
        "UPTIME_KUMA_ADMIN_USER",
        "UPTIME_KUMA_ADMIN_PASSWORD",
    ):
        if os.environ.get(key):
            cfg[key] = os.environ[key]

    # Fall back to SOPS if any required credentials are missing from .env
    needed = (
        "DISCORD_WEBHOOK_URL",
        "BESZEL_ADMIN_EMAIL",
        "BESZEL_ADMIN_PASSWORD",
        "UPTIME_KUMA_ADMIN_PASSWORD",
    )
    if any(not cfg.get(k) for k in needed) and SECRETS_FILE.exists():
        env_sops = os.environ.copy()
        if not env_sops.get("SOPS_AGE_KEY_FILE"):
            default_key = Path.home() / ".config" / "sops" / "age" / "keys.txt"
            if default_key.exists():
                env_sops["SOPS_AGE_KEY_FILE"] = str(default_key)
        try:
            raw = subprocess.check_output(
                ["sops", "-d", str(SECRETS_FILE)],
                env=env_sops,
                text=True,
                stderr=subprocess.DEVNULL,
            )
            secrets_data = yaml.safe_load(raw) or {}
            for k, v in secrets_data.items():
                if isinstance(v, (str, int, float, bool)):
                    cfg.setdefault(k.upper(), str(v))
        except (subprocess.CalledProcessError, FileNotFoundError):
            pass

    return cfg


def discord_webhook_to_shoutrrr(webhook_url: str) -> str:
    """Convert a Discord webhook URL to Beszel/Shoutrrr format."""
    match = re.match(
        r"https?://(?:discord\.com|discordapp\.com)/api/webhooks/([^/]+)/([^/?#]+)",
        webhook_url,
    )
    if not match:
        raise ValueError("Invalid Discord webhook URL format")
    webhook_id, webhook_token = match.group(1), match.group(2)
    return f"discord://{webhook_token}@{webhook_id}"


def _beszel_api(
    base_url: str,
    method: str,
    path: str,
    body: dict[str, Any] | None = None,
    token: str | None = None,
) -> dict[str, Any]:
    data = json.dumps(body).encode() if body is not None else None
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(
        f"{base_url}{path}", data=data, headers=headers, method=method
    )
    with urllib.request.urlopen(req, timeout=15) as resp:
        raw = resp.read().decode()
        return json.loads(raw) if raw else {}


def _container_running(name: str) -> bool:
    try:
        out = subprocess.check_output(
            ["docker", "inspect", "-f", "{{.State.Running}}", name],
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
        return out == "true"
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def sync_beszel(cfg: dict[str, str], discord_url: str) -> None:
    """Update Beszel user_settings Discord Shoutrrr webhook if changed."""
    if not _container_running("beszel"):
        print("Skipping Beszel webhook sync: container 'beszel' is not running")
        return

    domain = cfg.get("NEXUS_DOMAIN")
    email = cfg.get("BESZEL_ADMIN_EMAIL")
    password = cfg.get("BESZEL_ADMIN_PASSWORD")
    if not (domain and email and password):
        print("Skipping Beszel webhook sync: missing credentials or domain")
        return

    base_url = f"https://beszel.{domain}"
    shoutrrr_url = discord_webhook_to_shoutrrr(discord_url)

    # Wait briefly for Beszel to become reachable after deploy
    auth: dict[str, Any] | None = None
    for attempt in range(6):
        try:
            auth = _beszel_api(
                base_url,
                "POST",
                "/api/collections/users/auth-with-password",
                {"identity": email, "password": password},
            )
            break
        except (urllib.error.URLError, TimeoutError):
            if attempt == 5:
                raise
            time.sleep(3)

    assert auth is not None
    token = auth["token"]
    items = _beszel_api(
        base_url, "GET", "/api/collections/user_settings/records", token=token
    ).get("items", [])
    if not items:
        print("Skipping Beszel webhook sync: no user_settings record found")
        return

    rec = items[0]
    rec_id = rec["id"]
    settings: dict[str, Any] = rec.get("settings") or {}
    existing_webhooks: list[str] = list(settings.get("webhooks") or [])
    non_discord = [w for w in existing_webhooks if not w.startswith("discord://")]
    desired_webhooks = [*non_discord, shoutrrr_url]

    if existing_webhooks == desired_webhooks:
        print("Beszel Discord webhook is already up to date")
        return

    settings["webhooks"] = desired_webhooks
    _beszel_api(
        base_url,
        "PATCH",
        f"/api/collections/user_settings/records/{rec_id}",
        {"settings": settings},
        token=token,
    )
    print("Updated Beszel Discord webhook")


UPTIME_KUMA_SYNC_JS = r"""
const { io } = require("socket.io-client");
const socket = io("http://127.0.0.1:3001");
const emitAsync = (ev, ...args) => new Promise((r) => socket.emit(ev, ...args, r));
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

const NOTIF_NAME = "Discord (Nexus Alerts)";
const WEBHOOK_URL = process.env.DISCORD_WEBHOOK_URL;
const USER = process.env.UK_USER || "admin";
const PASS = process.env.UK_PASS;

socket.on("connect_error", (err) => {
  console.error("Uptime Kuma connect_error:", err.message);
  process.exit(1);
});

socket.on("connect", async () => {
  try {
    let notifs = [];
    socket.on("notificationList", (list) => { notifs = list || []; });

    const loginRes = await emitAsync("login", {
      username: USER,
      password: PASS,
      token: "",
    });
    if (!loginRes.ok) {
      throw new Error("Login failed: " + JSON.stringify(loginRes));
    }
    await sleep(1500);

    const existing = notifs.find((n) => n.name === NOTIF_NAME);
    if (existing) {
      let currentCfg = {};
      try { currentCfg = JSON.parse(existing.config || "{}"); } catch {}
      if (currentCfg.discordWebhookUrl === WEBHOOK_URL) {
        console.log("Uptime Kuma Discord webhook is already up to date");
        socket.close();
        process.exit(0);
      }
    }

    const notifConfig = {
      name: NOTIF_NAME,
      type: "discord",
      isDefault: true,
      applyExisting: true,
      active: true,
      discordWebhookUrl: WEBHOOK_URL,
      discordUsername: "Uptime Kuma (Nexus)",
      discordPrefixMessage: "",
    };

    const existingId = existing ? existing.id : null;
    const res = await emitAsync("addNotification", notifConfig, existingId);
    if (!res.ok) {
      throw new Error("addNotification failed: " + JSON.stringify(res));
    }
    const action = existing ? "Updated" : "Created";
    console.log(`${action} Uptime Kuma Discord webhook`);
    socket.close();
    process.exit(0);
  } catch (err) {
    console.error("Uptime Kuma sync error:", err.message || err);
    socket.close();
    process.exit(1);
  }
});
"""


def sync_uptime_kuma(cfg: dict[str, str], discord_url: str) -> None:
    """Update Uptime Kuma Discord notification webhook if changed."""
    if not _container_running("uptime-kuma"):
        print("Skipping Uptime Kuma webhook sync: container is not running")
        return

    user = cfg.get("UPTIME_KUMA_ADMIN_USER", "admin")
    password = cfg.get("UPTIME_KUMA_ADMIN_PASSWORD")
    if not password:
        print("Skipping Uptime Kuma webhook sync: missing admin password")
        return

    subprocess.run(
        [
            "docker",
            "exec",
            "-i",
            "-e",
            f"UK_USER={user}",
            "-e",
            f"UK_PASS={password}",
            "-e",
            f"DISCORD_WEBHOOK_URL={discord_url}",
            "uptime-kuma",
            "node",
            "-",
        ],
        input=UPTIME_KUMA_SYNC_JS,
        text=True,
        check=True,
    )


def main() -> int:
    """Sync Discord webhook URL to running Beszel and Uptime Kuma instances."""
    cfg = load_config()
    discord_url = cfg.get("DISCORD_WEBHOOK_URL", "").strip()
    if not discord_url:
        print("DISCORD_WEBHOOK_URL not set; skipping monitoring webhook sync")
        return 0

    sync_beszel(cfg, discord_url)
    sync_uptime_kuma(cfg, discord_url)
    return 0


if __name__ == "__main__":
    sys.exit(main())
