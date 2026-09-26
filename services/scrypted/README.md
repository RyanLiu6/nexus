# Scrypted

High-performance video integration platform and camera bridge running natively on macOS outside Docker.

## Architecture

- **Runtime:** Native macOS installation running directly on the host (outside Docker) for optimal hardware video acceleration (Metal, VideoToolbox).
- **Service Management:** Native macOS daemon managed via LaunchAgent (`~/Library/LaunchAgents/com.koushikdutta.scrypted.plist`).
- **Dashboard Port:** Native HTTPS on port `10443` (uses self-signed certificate).
- **Reverse Proxy:** Traefik dynamic file rules in `services/traefik/rules/scrypted.yml` proxying `scrypted.{{ env `NEXUS_DOMAIN` }}` to `https://host.docker.internal:10443`.
- **SSL / Insecure Transport:** Traefik uses `serversTransports` with `insecureSkipVerify: true` to trust Scrypted's local self-signed certificate while presenting a valid Let's Encrypt certificate on the external interface.
- **Access Control:** Tailscale authentication middleware (`tailscale-chain@file`), restricted to `admins`.

## Installation

Install Scrypted natively on macOS using the Invoke task:

```bash
inv install-scrypted
```

Or execute the installer script directly:

```bash
./scripts/install-scrypted.sh
```

## Service Management

Scrypted installs as a user LaunchAgent daemon:

```bash
# Check service status
launchctl list | grep scrypted

# Restart service
launchctl kickstart -k gui/$(id -u)/com.koushikdutta.scrypted

# View logs
tail -f ~/.scrypted/log.txt
```
