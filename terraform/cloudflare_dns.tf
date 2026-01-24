# =============================================================================
# DNS Records for Tailscale-Only Services
# These point directly to the Tailscale IP, not proxied through Cloudflare
# Only devices on Tailscale can reach these services
# =============================================================================

resource "cloudflare_record" "tailscale_subdomains" {
  for_each = var.tailscale_server_ip != "" ? var.subdomains : toset([])
  zone_id  = var.cloudflare_zone_id
  name     = each.key
  content  = var.tailscale_server_ip
  type     = "A"
  ttl      = 1
  proxied  = false # Cannot proxy to private Tailscale IP
}

# =============================================================================
# Variables
# =============================================================================

variable "subdomains" {
  description = "List of subdomains to create DNS records for"
  type        = set(string)
  default     = []
}
