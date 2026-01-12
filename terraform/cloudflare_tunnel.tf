# Cloudflare Tunnel Configuration
# This creates and manages a Cloudflare Tunnel for zero-port-forwarding access
# Only created when use_tunnel = true

# Tunnel for the nexus homelab
resource "cloudflare_zero_trust_tunnel_cloudflared" "nexus" {
  count      = var.use_tunnel ? 1 : 0
  account_id = var.cloudflare_account_id
  name       = "nexus-${var.domain}"
  secret     = base64encode(var.tunnel_secret)
}

# Tunnel configuration - routes all subdomains through the tunnel
resource "cloudflare_zero_trust_tunnel_cloudflared_config" "nexus" {
  count      = var.use_tunnel ? 1 : 0
  account_id = var.cloudflare_account_id
  tunnel_id  = cloudflare_zero_trust_tunnel_cloudflared.nexus[0].id

  config {
    # Wildcard route for all subdomains
    ingress_rule {
      hostname = "*.${var.domain}"
      service  = "http://localhost:80"
    }

    # Root domain route
    ingress_rule {
      hostname = var.domain
      service  = "http://localhost:80"
    }

    # Catch-all (required by Cloudflare)
    ingress_rule {
      service = "http_status:404"
    }
  }
}

# DNS CNAME record pointing root domain to the tunnel
resource "cloudflare_record" "tunnel_root" {
  count   = var.use_tunnel ? 1 : 0
  zone_id = var.cloudflare_zone_id
  name    = "@"
  content = "${cloudflare_zero_trust_tunnel_cloudflared.nexus[0].id}.cfargotunnel.com"
  type    = "CNAME"
  ttl     = 1
  proxied = true
}

# DNS CNAME record pointing wildcard to the tunnel
resource "cloudflare_record" "tunnel_wildcard" {
  count   = var.use_tunnel ? 1 : 0
  zone_id = var.cloudflare_zone_id
  name    = "*"
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
