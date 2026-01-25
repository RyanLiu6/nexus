terraform {
  required_providers {
    cloudflare = {
      source  = "cloudflare/cloudflare"
      version = "~> 5.0"
    }
    tailscale = {
      source  = "tailscale/tailscale"
      version = "~> 0.25"
    }
  }

  required_version = ">= 1.0"
}

provider "cloudflare" {
  api_token = var.cloudflare_api_token
}

provider "tailscale" {
  api_key = var.tailscale_api_key
  tailnet = var.tailnet_id
}

# =============================================================================
# Required Variables
# =============================================================================

variable "cloudflare_api_token" {
  description = "Cloudflare API token with Account permissions (Tunnel:Edit, R2:Edit) and User permissions (API Tokens:Read, API Tokens:Edit)"
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
# Cloudflare Tunnel Configuration
# =============================================================================

variable "tunnel_secret" {
  description = "Secret for the Cloudflare Tunnel (generate with: openssl rand -hex 32)"
  type        = string
  sensitive   = true
  default     = ""
}

# =============================================================================
# Tailscale Configuration
# =============================================================================

variable "tailscale_api_key" {
  description = "Tailscale API key for managing ACLs and DNS"
  type        = string
  sensitive   = true
  default     = ""
}

variable "tailnet_id" {
  description = "Tailnet ID (found at admin/settings/general)"
  type        = string
  default     = ""
}

variable "tailscale_users" {
  description = "Map of group names to lists of user emails for Tailscale ACL"
  type        = map(list(string))
  default     = {}
}
