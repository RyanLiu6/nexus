# Cloudflared - Cloudflare Tunnel

Secure tunnel for public access to services without port forwarding.

## What It Does

Connects your homelab to Cloudflare's network via an outbound-only connection, allowing
public access to designated services (like FoundryVTT) without exposing your home IP.

## Prerequisites

- Cloudflare account with your domain
- Tunnel credentials from Terraform (auto-configured during deploy)

## Configuration

The tunnel token is automatically retrieved from Terraform outputs during deployment.
No manual configuration needed.

## Environment Variables

| Variable | Description |
|----------|-------------|
| `TUNNEL_TOKEN` | Cloudflare Tunnel token (from terraform output) |

## How It Works

1. Terraform creates the tunnel in Cloudflare
2. Deploy retrieves the tunnel token
3. Cloudflared connects using the token
4. Public DNS records point to Cloudflare
5. Cloudflare routes traffic through the tunnel to Traefik
