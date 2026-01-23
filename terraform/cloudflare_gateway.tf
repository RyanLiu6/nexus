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
      enabled = false
    }
    ipv6 {
      enabled = false
    }
  }
}

# =============================================================================
# Gateway Policies (DNS Firewall Rules)
# =============================================================================
# Category IDs from: https://developers.cloudflare.com/cloudflare-one/policies/gateway/domain-categories/
# Recommended policy from: https://developers.cloudflare.com/learning-paths/secure-internet-traffic/build-dns-policies/recommended-dns-policies/

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
  value       = var.enable_gateway ? "https://${cloudflare_zero_trust_dns_location.tailscale[0].id}.cloudflare-gateway.com/dns-query" : ""
}

# Note: The IPv4/IPv6 DNS endpoints are assigned by Cloudflare and shown in the
# Zero Trust dashboard under Gateway → DNS Locations after applying.
# Configure these IPs in Tailscale Admin → DNS → Global Nameservers.
