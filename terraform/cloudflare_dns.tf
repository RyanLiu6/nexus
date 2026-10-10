# =============================================================================
# DNS Records for Tailscale-Only Services
# These point directly to the Tailscale IP, not proxied through Cloudflare
# Only devices on Tailscale can reach these services
# =============================================================================

resource "cloudflare_dns_record" "tailscale_subdomains" {
  for_each = var.tailscale_server_ip != "" ? var.subdomains : toset([])
  zone_id  = var.cloudflare_zone_id
  name     = each.key
  content  = var.tailscale_server_ip
  type     = "A"
  ttl      = 1
  proxied  = false # Cannot proxy to private Tailscale IP
}

resource "cloudflare_dns_record" "headplane" {
  zone_id = var.cloudflare_zone_id
  name    = "headplane"
  content = var.tailscale_server_ip
  type    = "A"
  ttl     = 1
  proxied = false
}

# =============================================================================
# Variables
# =============================================================================

variable "tailscale_server_ip" {
  description = "Tailscale IP of the Nexus server"
  type        = string
  default     = ""
}

variable "subdomains" {
  description = "List of subdomains to create DNS records for"
  type        = set(string)
  default     = []
}

# =============================================================================
# Headscale Direct Record (UDP Support)
# =============================================================================
# Why is this manually defined instead of using `public_subdomains`?
# The `public_subdomains` block automatically applies `proxied = true` (Cloudflare's orange cloud).
# Cloudflare proxy only supports HTTP/HTTPS (TCP 80/443). However, Headscale/Tailscale
# requires UDP traffic for peer-to-peer Wireguard tunnels and STUN negotiation.
# By manually creating this record with `proxied = false`, we expose the raw IP,
# allowing UDP traffic to flow natively and preventing forced TCP relays.
resource "cloudflare_dns_record" "headscale_direct" {
  zone_id = var.cloudflare_zone_id
  name    = "headscale"
  content = trimspace(data.http.myip.response_body)
  type    = "A"
  ttl     = 1
  proxied = false
}
