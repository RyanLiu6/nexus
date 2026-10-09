# Headscale

[Headscale](https://headscale.net/) is an open-source, self-hosted implementation of the Tailscale control server.

It replaces the commercial Tailnet and coordinates encrypted WireGuard connections between all your devices on the local machine and remote clients.

## Architecture & Integration in Nexus

- **Control Plane**: Headscale runs as a core container dependency behind Traefik.
- **Port 8080**: Serves Headscale HTTP/WebSocket control plane API via Traefik (`https://headscale.<domain>`).
- **Port 3478/UDP**: STUN endpoint for NAT traversal and DERP relaying.
- **Web UI (Headplane)**: Serves a Tailscale admin console clone via Traefik (`https://headplane.<domain>`).
- **ACL Policy**: Loaded from `tailscale/acl.hujson`, generated from user groups configured in `ansible/vars/vault.yml`.
- **Identity & Authentication**: The host's `tailscaled` daemon connects to Headscale as the coordination server. Downstream, `tailscale-access` queries `tailscaled`'s LocalAPI socket (`/var/run/tailscale/tailscaled.sock`) to authenticate requests.

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

## OIDC Authentication with Google

Headscale natively supports OpenID Connect (OIDC). Enabling OIDC allows users and devices to sign in using their identity provider directly in the browser when running `tailscale up`, exactly like standard Tailscale SaaS.

For a complete step-by-step guide on configuring Google Workspace or Gmail as your OIDC provider, including cost analysis and configuration snippets, please see the [OIDC Authentication Guide](OIDC.md).
