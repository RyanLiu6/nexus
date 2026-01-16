# Cloudflare Tunnel Configuration
# This creates and manages a Cloudflare Tunnel for zero-port-forwarding access
# Only created when use_tunnel = true
#
# SECURITY MODEL:
# - Only FoundryVTT is publicly accessible via Cloudflare Tunnel
# - All other services require Tailscale VPN access
# - FoundryVTT has its own authentication system

# Tunnel for the nexus homelab
resource "cloudflare_zero_trust_tunnel_cloudflared" "nexus" {
  count      = var.use_tunnel ? 1 : 0
  account_id = var.cloudflare_account_id
  name       = "nexus-${var.domain}"
  secret     = base64encode(var.tunnel_secret)
}

# Tunnel configuration - only routes FoundryVTT through the tunnel
resource "cloudflare_zero_trust_tunnel_cloudflared_config" "nexus" {
  count      = var.use_tunnel ? 1 : 0
  account_id = var.cloudflare_account_id
  tunnel_id  = cloudflare_zero_trust_tunnel_cloudflared.nexus[0].id

  config {
    # FoundryVTT - the only publicly accessible service
    # Has its own authentication system for game sessions
    ingress_rule {
      hostname = "foundry.${var.domain}"
      service  = "http://localhost:80"
    }

    # Catch-all - return 403 for any other subdomain
    # All other services require Tailscale access
    ingress_rule {
      service = "http_status:403"
    }
  }
}

# DNS CNAME record for FoundryVTT pointing to the tunnel
resource "cloudflare_record" "tunnel_foundry" {
  count   = var.use_tunnel ? 1 : 0
  zone_id = var.cloudflare_zone_id
  name    = "foundry"
  content = "${cloudflare_zero_trust_tunnel_cloudflared.nexus[0].id}.cfargotunnel.com"
  type    = "CNAME"
  ttl     = 1
  proxied = true
}

# Output the tunnel token for cloudflared to use
output "tunnel_token" {
  value     = var.use_tunnel ? cloudflare_zero_trust_tunnel_cloudflared.nexus[0].tunnel_token : ""
  sensitive = true
}

output "tunnel_id" {
  value = var.use_tunnel ? cloudflare_zero_trust_tunnel_cloudflared.nexus[0].id : ""
}
