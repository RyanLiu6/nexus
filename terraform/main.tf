terraform {
  required_providers {
    cloudflare = {
      source  = "cloudflare/cloudflare"
      version = "~> 4.0"
    }
  }

  required_version = ">= 1.0"
}

provider "cloudflare" {
  api_token = var.cloudflare_api_token
}

# =============================================================================
# Required Variables
# =============================================================================

variable "cloudflare_api_token" {
  description = "Cloudflare API token with Zone:DNS:Edit, Zone:Zone:Read, and Account:Cloudflare Tunnel:Edit permissions"
  type        = string
  sensitive   = true
}

variable "cloudflare_zone_id" {
  description = "Cloudflare Zone ID for your domain"
  type        = string
  sensitive   = true
}

variable "cloudflare_account_id" {
  description = "Cloudflare Account ID (required for tunnel management)"
  type        = string
  sensitive   = true
}

variable "domain" {
  description = "Base domain (e.g., example.com)"
  type        = string
}

# =============================================================================
# Cloudflare Tunnel Configuration (Recommended)
# =============================================================================

variable "use_tunnel" {
  description = "Use Cloudflare Tunnel instead of port forwarding (recommended)"
  type        = bool
  default     = true
}

variable "tunnel_secret" {
  description = "Secret for the Cloudflare Tunnel (generate with: openssl rand -hex 32)"
  type        = string
  sensitive   = true
  default     = ""
}

# =============================================================================
# Port Forwarding Configuration (Legacy)
# Only used when use_tunnel = false
# =============================================================================

variable "public_ip" {
  description = "Public IP address for DNS A records (only if not using tunnel)"
  type        = string
  default     = ""
}

variable "subdomains" {
  description = "List of subdomains to create A records for (only if not using tunnel)"
  type        = set(string)
  default     = []
}

variable "proxied" {
  description = "Whether to proxy through Cloudflare (Orange Cloud)"
  type        = bool
  default     = true
}
