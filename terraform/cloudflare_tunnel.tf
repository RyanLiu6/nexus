# Cloudflare Tunnel Configuration
# This creates and manages a Cloudflare Tunnel for zero-port-forwarding access
#
# SECURITY MODEL:
# - Only FoundryVTT is publicly accessible via Cloudflare Tunnel
# - All other services require Tailscale VPN access
# - FoundryVTT has its own authentication system

locals {
  tunnel_enabled = var.tunnel_secret != ""
}

# Tunnel for the nexus homelab
resource "cloudflare_zero_trust_tunnel_cloudflared" "nexus" {
  count      = local.tunnel_enabled ? 1 : 0
  account_id = var.cloudflare_account_id
  name       = "nexus-${var.domain}"
  tunnel_secret = base64encode(var.tunnel_secret)
}

# Tunnel configuration - only routes FoundryVTT through the tunnel
resource "cloudflare_zero_trust_tunnel_cloudflared_config" "nexus" {
  count      = local.tunnel_enabled ? 1 : 0
  account_id = var.cloudflare_account_id
  tunnel_id  = cloudflare_zero_trust_tunnel_cloudflared.nexus[0].id

  config = {
    ingress = [
      {
        hostname = "foundry.${var.domain}"
        service  = "http://localhost:80"
      },
      {
        service = "http_status:403"
      }
    ]
  }
}

data "cloudflare_zero_trust_tunnel_cloudflared_token" "nexus" {
  count      = local.tunnel_enabled ? 1 : 0
  account_id = var.cloudflare_account_id
  tunnel_id  = cloudflare_zero_trust_tunnel_cloudflared.nexus[0].id
}

# DNS CNAME record for FoundryVTT pointing to the tunnel
resource "cloudflare_dns_record" "tunnel_foundry" {
  count   = local.tunnel_enabled ? 1 : 0
  zone_id = var.cloudflare_zone_id
  name    = "foundry"
  content = "${cloudflare_zero_trust_tunnel_cloudflared.nexus[0].id}.cfargotunnel.com"
  type    = "CNAME"
  ttl     = 1
  proxied = true
}

# Output the tunnel token for cloudflared to use
output "tunnel_token" {
  value     = local.tunnel_enabled ? data.cloudflare_zero_trust_tunnel_cloudflared_token.nexus[0].token : ""
  sensitive = true
}

output "tunnel_id" {
  value     = local.tunnel_enabled ? cloudflare_zero_trust_tunnel_cloudflared.nexus[0].id : ""
  sensitive = true
}
