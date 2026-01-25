# =============================================================================
# Cloudflare R2 Storage for Foundry VTT
# =============================================================================
# Provisions an R2 bucket and API token for S3-compatible access.
# Credentials are output for injection into Ansible/Foundry configuration.

resource "cloudflare_r2_bucket" "foundry" {
  account_id = var.cloudflare_account_id
  name       = "foundry-assets"
  location   = "WNAM"  # Western North America
}

# API Token with R2 read/write permissions for S3-compatible access
resource "cloudflare_api_token" "r2_access" {
  name = "foundry-r2-access"

  policies = [{
    permission_groups = [
      { id = one([for p in data.cloudflare_account_api_token_permission_groups_list.all.result : p.id if p.name == "Workers R2 Storage Bucket Item Read"]) },
      { id = one([for p in data.cloudflare_account_api_token_permission_groups_list.all.result : p.id if p.name == "Workers R2 Storage Bucket Item Write"]) },
    ]
    resources = {
      "com.cloudflare.edge.r2.bucket.${var.cloudflare_account_id}_default_${cloudflare_r2_bucket.foundry.name}" = "*"
    }
    effect = "allow"
  }]
}

# Get available permission groups
data "cloudflare_account_api_token_permission_groups_list" "all" {
  account_id = var.cloudflare_account_id
}

# =============================================================================
# Outputs for Ansible/Foundry Configuration
# =============================================================================

output "foundry_r2_endpoint" {
  description = "R2 S3-compatible endpoint URL"
  value       = "https://${var.cloudflare_account_id}.r2.cloudflarestorage.com"
  sensitive   = true
}

output "foundry_r2_access_key" {
  description = "R2 access key ID (API token ID)"
  value       = cloudflare_api_token.r2_access.id
  sensitive   = true
}

output "foundry_r2_secret_key" {
  description = "R2 secret access key (API token value)"
  value       = cloudflare_api_token.r2_access.value
  sensitive   = true
}

output "foundry_r2_bucket" {
  description = "R2 bucket name"
  value       = cloudflare_r2_bucket.foundry.name
}
