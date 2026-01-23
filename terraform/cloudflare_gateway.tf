# Cloudflare Zero Trust Gateway Configuration
# DNS filtering for ad-blocking, malware protection, and content filtering
#
# This replaces NextDNS by configuring Cloudflare Gateway as the DNS resolver
# for all Tailscale-connected devices.
#
# Category IDs reference:
# https://developers.cloudflare.com/cloudflare-one/policies/gateway/domain-categories/

# =============================================================================
# Variables
# =============================================================================

variable "enable_gateway" {
  description = "Enable Cloudflare Gateway DNS filtering"
  type        = bool
  default     = true
}

variable "tailscale_server_ip" {
  description = "Tailscale IP of the Nexus server (for DNS override of subdomains)"
  type        = string
  default     = ""
}

variable "gateway_block_ads" {
  description = "Block advertisements and trackers"
  type        = bool
  default     = true
}

variable "gateway_block_malware" {
  description = "Block malware, phishing, and security threats"
  type        = bool
  default     = true
}

variable "gateway_block_adult_content" {
  description = "Block adult and inappropriate content"
  type        = bool
  default     = true
}

# =============================================================================
# DNS Location
# =============================================================================

# Creates a DNS Location that provides unique DNS endpoints
# These endpoints are configured in Tailscale as global nameservers
resource "cloudflare_zero_trust_dns_location" "tailscale" {
  count          = var.enable_gateway ? 1 : 0
  account_id     = var.cloudflare_account_id
  name           = "Tailscale Network"
  client_default = true
  ecs_support    = false

  endpoints {
    doh {
      enabled = true
    }
    dot {
      enabled = true
    }
    ipv4 {
      enabled = true
    }
    ipv6 {
      enabled = true
    }
  }
}

# =============================================================================
# Gateway Policies (DNS Firewall Rules)
# =============================================================================
# Category IDs from: https://developers.cloudflare.com/cloudflare-one/policies/gateway/domain-categories/
# Recommended policy from: https://developers.cloudflare.com/learning-paths/secure-internet-traffic/build-dns-policies/recommended-dns-policies/

# Policy 0: Resolve subdomains to Tailscale server (Split DNS)
# Matches *.domain.com but NOT domain.com itself (apex is Cloudflare Pages)
resource "cloudflare_zero_trust_gateway_policy" "resolve_subdomains" {
  count       = var.enable_gateway && var.tailscale_server_ip != "" ? 1 : 0
  account_id  = var.cloudflare_account_id
  name        = "Resolve ${var.domain} subdomains"
  description = "Route *.${var.domain} to Tailscale server for local services"
  precedence  = 0
  action      = "allow"
  enabled     = true

  filters = ["dns"]

  # Match any subdomain of the domain (e.g., grafana.example.com)
  # Does NOT match the apex domain (example.com)
  traffic = "dns.fqdn matches \".*\\\\.${replace(var.domain, ".", "\\\\.")}$\""

  rule_settings {
    override_ips = [var.tailscale_server_ip]
  }
}

# Policy 1: Block Security Threats
# Uses Cloudflare's recommended security category blocklist
# IDs: 68=Anonymizer, 80=C2/Botnet, 83=Cryptomining, 117=Malware, 131=Phishing,
#      134=Private IP, 151=Spam, 153=Spyware, 175=DNS Tunneling, 176=DGA, 178=Brand Embedding
resource "cloudflare_zero_trust_gateway_policy" "block_security_threats" {
  count       = var.enable_gateway && var.gateway_block_malware ? 1 : 0
  account_id  = var.cloudflare_account_id
  name        = "Block Security Threats"
  description = "Block malware, phishing, and other security threats"
  precedence  = 1
  action      = "block"
  enabled     = true

  filters = ["dns"]

  # Cloudflare's recommended security categories blocklist
  traffic = "any(dns.security_category[*] in {68 80 83 117 131 134 151 153 175 176 178})"

  rule_settings {
    block_page_enabled = false
  }
}

# Policy 2: Block Ads and Trackers
# ID: 66=Advertisements
resource "cloudflare_zero_trust_gateway_policy" "block_ads" {
  count       = var.enable_gateway && var.gateway_block_ads ? 1 : 0
  account_id  = var.cloudflare_account_id
  name        = "Block Ads & Trackers"
  description = "Block advertisements and tracking domains"
  precedence  = 2
  action      = "block"
  enabled     = true

  filters = ["dns"]

  traffic = "any(dns.content_category[*] in {66})"

  rule_settings {
    block_page_enabled = false
  }
}

# Policy 3: Block Adult and Inappropriate Content
# IDs: 67=Adult Themes, 84=Dating, 87=Drugs, 99=Gambling, 125=Nudity, 133=Pornography
resource "cloudflare_zero_trust_gateway_policy" "block_adult_content" {
  count       = var.enable_gateway && var.gateway_block_adult_content ? 1 : 0
  account_id  = var.cloudflare_account_id
  name        = "Block Adult & Inappropriate Content"
  description = "Block adult themes, gambling, and other inappropriate content"
  precedence  = 3
  action      = "block"
  enabled     = true

  filters = ["dns"]

  traffic = "any(dns.content_category[*] in {67 84 87 99 125 133})"

  rule_settings {
    block_page_enabled = false
  }
}

# =============================================================================
# Outputs
# =============================================================================

output "gateway_location_id" {
  description = "DNS Location ID for Cloudflare Gateway"
  value       = var.enable_gateway ? cloudflare_zero_trust_dns_location.tailscale[0].id : ""
}

output "gateway_doh_endpoint" {
  description = "DNS over HTTPS endpoint for this location"
  value       = var.enable_gateway ? "https://${cloudflare_zero_trust_dns_location.tailscale[0].doh_subdomain}.cloudflare-gateway.com/dns-query" : ""
}

output "gateway_ipv4_primary" {
  description = "Primary IPv4 DNS address for Tailscale"
  value       = var.enable_gateway ? cloudflare_zero_trust_dns_location.tailscale[0].ipv4_destination : ""
}

output "gateway_ipv4_backup" {
  description = "Backup IPv4 DNS address for Tailscale"
  value       = var.enable_gateway ? cloudflare_zero_trust_dns_location.tailscale[0].ipv4_destination_backup : ""
}
