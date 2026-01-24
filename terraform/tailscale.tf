# Tailscale Configuration
# Manages ACL policy and DNS settings via Terraform
#
# Documentation: https://registry.terraform.io/providers/tailscale/tailscale/latest/docs

# =============================================================================
# Variables
# =============================================================================

variable "enable_tailscale" {
  description = "Enable Tailscale ACL and DNS management"
  type        = bool
  default     = true
}

# =============================================================================
# Locals - Build ACL Policy from tailscale_users
# =============================================================================

locals {
  # Only enable if API key is configured
  tailscale_enabled = var.enable_tailscale && var.tailscale_api_key != "" && length(var.tailscale_users) > 0

  # Build groups with "group:" prefix
  acl_groups = {
    for name, emails in var.tailscale_users : "group:${name}" => emails
  }

  # Non-admin groups (get web-only access)
  non_admin_groups = [
    for name in keys(var.tailscale_users) : name if name != "admins"
  ]

  # Build ACL rules
  # - admins get full access to all ports + SSH
  # - other groups get web-only access (ports 80, 443)
  acl_rules = concat(
    # Admin rule: full access
    contains(keys(var.tailscale_users), "admins") ? [
      {
        action = "accept"
        src    = ["group:admins"]
        dst    = ["tag:nexus-server:*"]
      }
    ] : [],
    # Non-admin rules: web-only access
    [
      for name in local.non_admin_groups : {
        action = "accept"
        src    = ["group:${name}"]
        dst    = ["tag:nexus-server:80", "tag:nexus-server:443"]
      }
    ]
  )

  # SSH rules (admins only)
  ssh_rules = contains(keys(var.tailscale_users), "admins") ? [
    {
      action = "accept"
      src    = ["group:admins"]
      dst    = ["tag:nexus-server"]
      users  = ["autogroup:nonroot", "root"]
    }
  ] : []

  # Complete ACL policy
  acl_policy = {
    groups = local.acl_groups
    tagOwners = {
      "tag:nexus-server" = ["group:admins"]
    }
    acls = local.acl_rules
    ssh  = local.ssh_rules
  }
}

# =============================================================================
# ACL Policy
# =============================================================================

resource "tailscale_acl" "nexus" {
  count = local.tailscale_enabled ? 1 : 0

  acl = jsonencode(local.acl_policy)
}

# =============================================================================
# DNS Configuration
# =============================================================================

# Configure global nameservers to use Cloudflare Gateway (if available)
resource "tailscale_dns_nameservers" "global" {
  count = local.tailscale_enabled && var.enable_gateway ? 1 : 0

  nameservers = compact([
    var.enable_gateway ? cloudflare_zero_trust_dns_location.tailscale[0].ipv4_destination : "",
    var.enable_gateway ? cloudflare_zero_trust_dns_location.tailscale[0].ipv4_destination_backup : "",
  ])
}

# Enable MagicDNS and override local DNS
resource "tailscale_dns_preferences" "main" {
  count = local.tailscale_enabled ? 1 : 0

  magic_dns = true
}

# =============================================================================
# Outputs
# =============================================================================

output "tailscale_acl_applied" {
  description = "Whether Tailscale ACL was applied"
  value       = local.tailscale_enabled
  sensitive   = true
}

output "tailscale_groups" {
  description = "Groups configured in Tailscale ACL"
  value       = local.tailscale_enabled ? keys(var.tailscale_users) : []
  sensitive   = true
}
