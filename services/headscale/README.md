# Headscale

[Headscale](https://headscale.net/) is an open-source, self-hosted implementation of the Tailscale control server.

It replaces the commercial Tailnet and coordinates encrypted WireGuard connections between all your devices on the local machine and remote clients.

## Architecture & Integration in Nexus

- **Control Plane**: Headscale runs as a core container dependency behind Traefik.
- **Port 8080**: Serves Headscale HTTP/WebSocket control plane API via Traefik (`https://headscale.<domain>`).
- **Port 3478/UDP**: STUN endpoint for NAT traversal and DERP relaying.
- **Web UI (Headplane)**: Serves a Tailscale admin console clone via Traefik (`https://headplane.<domain>`).
- **ACL Policy**: Loaded from `tailscale/acl.hujson`, generated from user groups configured in `config/secrets.yml`.
- **Identity & Authentication**: The host's `tailscaled` daemon connects to Headscale as the coordination server. Downstream, `authentik` queries `tailscaled`'s LocalAPI socket (`/var/run/tailscale/tailscaled.sock`) to authenticate requests.

## Deployment

Deploy with the core or home preset:

```bash
inv deploy --preset core
# or
inv deploy --preset home
```

---

## Headplane Web UI (Tailscale Console Replacement)

Nexus bundles **[Headplane](https://github.com/tale/headplane)**, an open-source web console replica of the official Tailscale dashboard.

### Accessing the Web UI

- **URL**: `https://headplane.<your-domain>`
- **Security**: The UI router is protected by Traefik's `tailscale-chain` ForwardAuth middleware, ensuring only authenticated VPN users with admin privileges can load the page.

### First-Time Login / API Key Generation

Headplane authenticates with the Headscale control server using an API key.

1. Generate a long-lived Headscale API key:
   ```bash
   docker exec headscale headscale apikeys create --expiration 90d
   ```
2. Navigate to `https://headplane.<your-domain>`.
3. Paste the generated API key into the login prompt to access the full visual dashboard (nodes, users, routes, pre-auth keys, and settings).

---

## Setup & Connecting Devices

### 1. Connect the Nexus Server (One-Time)

Connect the host server to your local Headscale control server:

```bash
sudo tailscale up --login-server https://headscale.<your-domain> --advertise-tags=tag:nexus-server --ssh
```

### 2. User Management (CLI)

Manage users via `docker exec`:

```bash
# Create a user
docker exec headscale headscale users create <username>

# List users
docker exec headscale headscale users list
```

### 3. Registering Client Devices

**Option A: OIDC Authentication (Recommended)**

Since OIDC is configured, simply run:
```bash
tailscale up --login-server https://headscale.<your-domain>
```
Follow the web link provided to authenticate via Google.

**Option B: Pre-authenticated Key (For unattended servers)**

```bash
# Generate a reusable preauth key valid for 24 hours
docker exec headscale headscale preauthkeys create --user <username> --reusable --expiration 24h

# Connect client using the key
tailscale up --login-server https://headscale.<your-domain> --authkey <key>
```

### 4. Viewing Connected Nodes

```bash
docker exec headscale headscale nodes list
```

---

## OIDC Authentication & User Access Control

We had to explicitly set up OpenID Connect (OIDC) using Google to handle authentication for our Tailscale clients. Since Headscale replaces the commercial Tailscale backend, we needed a way to securely authenticate users before they are allowed to join the private network.

By setting up OIDC, users authenticate directly via their Google account in the browser. Furthermore, Headscale is configured with an explicit `allowed_users` list derived directly from our `vault.yml` (`tailscale_users`). This acts as an automated bouncer: if someone successfully authenticates via Google but is not explicitly listed as an admin or member in our PyInfra configuration, Headscale immediately denies them network access.

For detailed setup instructions, please see the [OIDC Authentication Guide](OIDC.md).

---

## Network Security & Port Forwarding

To allow remote Tailscale clients to securely reach the Headscale control server and establish VPN tunnels, **port forwarding must be configured on your physical router.**

You must forward the following ports to your server's internal IP address:

*   **Port `443` (TCP/HTTPS)**: This is required so external clients can communicate with the Headscale control API securely. It's also used for the Traefik reverse proxy to handle the OIDC login callbacks, and to serve FoundryVTT.
*   **Port `26478` (UDP)**: This port handles Headscale's embedded DERP (Designated Encrypted Relay for Packets) server and STUN functionality. It is critical for NAT traversal, allowing remote peer devices to negotiate direct WireGuard connections with each other even when both are behind restrictive firewalls.

**Important:** Port `80` (HTTP) is **explicitly NOT port forwarded** by design. We rely entirely on DNS-01 challenges via Cloudflare to obtain our SSL certificates natively in Traefik, eliminating the need to expose insecure HTTP traffic or perform HTTP-01 challenges. Traefik automatically routes valid HTTPS traffic securely.
