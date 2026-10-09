terraform {
  required_providers {
    cloudflare = {
      source  = "cloudflare/cloudflare"
      version = "~> 5.18"
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
