# =============================================================================
# DNS Records for Port Forwarding (Legacy)
# Only created when use_tunnel = false
# =============================================================================

# Root domain A record (only if not using tunnel)
resource "cloudflare_record" "root" {
  count   = var.use_tunnel ? 0 : 1
  zone_id = var.cloudflare_zone_id
  name    = "@"
  content = var.public_ip
  type    = "A"
  ttl     = 1
  proxied = var.proxied
}

# Wildcard subdomain A record (only if not using tunnel)
resource "cloudflare_record" "wildcard" {
  count   = var.use_tunnel ? 0 : 1
  zone_id = var.cloudflare_zone_id
  name    = "*"
  content = var.public_ip
  type    = "A"
  ttl     = 1
  proxied = var.proxied
}

# Subdomain records - only if not using tunnel
resource "cloudflare_record" "subdomains" {
  for_each = var.use_tunnel ? toset([]) : var.subdomains
  zone_id  = var.cloudflare_zone_id
  name     = each.key
  content  = var.public_ip
  type     = "A"
  ttl      = 1
  proxied  = var.proxied
}

# =============================================================================
# DNS Records for Tailscale-Only Services (Tunnel Mode)
# These point directly to the Tailscale IP, not proxied through Cloudflare
# Only devices on Tailscale can reach these services
# =============================================================================

resource "cloudflare_record" "tailscale_subdomains" {
  for_each = var.use_tunnel && var.tailscale_server_ip != "" ? var.subdomains : toset([])
  zone_id  = var.cloudflare_zone_id
  name     = each.key
  content  = var.tailscale_server_ip
  type     = "A"
  ttl      = 1
  proxied  = false # Cannot proxy to private Tailscale IP
}
