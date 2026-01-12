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

variable "cloudflare_api_token" {
  description = "Cloudflare API token with Zone:DNS and Zone:Zone permissions"
  type        = string
  sensitive   = true
}

variable "cloudflare_zone_id" {
  description = "Cloudflare Zone ID for your domain"
  type        = string
  sensitive   = true
}

variable "domain" {
  description = "Base domain (e.g., ryanliu6.xyz)"
  type        = string
}

variable "subdomains" {
  description = "List of subdomains to create A records for"
  type        = set(string)
}

variable "public_ip" {
  description = "Public IP address for DNS records"
  type        = string
}

variable "proxied" {
  description = "Whether to proxy through Cloudflare (Orange Cloud)"
  type        = bool
  default     = false
}
