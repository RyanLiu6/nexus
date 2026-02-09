# =============================================================================
# Cloudflare R2 Storage
# =============================================================================
# Provisions R2 buckets and API tokens for S3-compatible access.
# Credentials are output for injection into Ansible/service configuration.

# Get available permission groups
data "cloudflare_api_token_permission_groups_list" "all" {}

# =============================================================================
# Foundry VTT R2 Storage
# =============================================================================

resource "cloudflare_r2_bucket" "foundry" {
  account_id = var.cloudflare_account_id
  name       = "foundry-assets"
  location   = "WNAM"  # Western North America
}

resource "cloudflare_api_token" "foundry_r2_access" {
  name = "foundry-r2-access"

  policies = [{
    permission_groups = [
      { id = one([for p in data.cloudflare_api_token_permission_groups_list.all.result : p.id if p.name == "Workers R2 Storage Bucket Item Read"]) },
      { id = one([for p in data.cloudflare_api_token_permission_groups_list.all.result : p.id if p.name == "Workers R2 Storage Bucket Item Write"]) },
    ]
    resources = jsonencode({
      "com.cloudflare.edge.r2.bucket.${var.cloudflare_account_id}_default_${cloudflare_r2_bucket.foundry.name}" = "*"
    })
    effect = "allow"
  }]
}

output "foundry_r2_endpoint" {
  description = "R2 S3-compatible endpoint URL"
  value       = "https://${var.cloudflare_account_id}.r2.cloudflarestorage.com"
  sensitive   = true
}

output "foundry_r2_access_key" {
  description = "R2 access key ID (API token ID)"
  value       = cloudflare_api_token.foundry_r2_access.id
  sensitive   = true
}

output "foundry_r2_secret_key" {
  description = "R2 secret access key (SHA-256 hash of API token value)"
  value       = sha256(cloudflare_api_token.foundry_r2_access.value)
  sensitive   = true
}

output "foundry_r2_bucket" {
  description = "R2 bucket name"
  value       = cloudflare_r2_bucket.foundry.name
}

# =============================================================================
# Donetick R2 Storage
# =============================================================================

resource "cloudflare_r2_bucket" "donetick" {
  account_id = var.cloudflare_account_id
  name       = "donetick-storage"
  location   = "WNAM"  # Western North America
}

resource "cloudflare_api_token" "donetick_r2_access" {
  name = "donetick-r2-access"

  policies = [{
    permission_groups = [
      { id = one([for p in data.cloudflare_api_token_permission_groups_list.all.result : p.id if p.name == "Workers R2 Storage Bucket Item Read"]) },
      { id = one([for p in data.cloudflare_api_token_permission_groups_list.all.result : p.id if p.name == "Workers R2 Storage Bucket Item Write"]) },
    ]
    resources = jsonencode({
      "com.cloudflare.edge.r2.bucket.${var.cloudflare_account_id}_default_${cloudflare_r2_bucket.donetick.name}" = "*"
    })
    effect = "allow"
  }]
}

output "donetick_r2_endpoint" {
  description = "R2 S3-compatible endpoint URL for Donetick"
  value       = "https://${var.cloudflare_account_id}.r2.cloudflarestorage.com"
  sensitive   = true
}

output "donetick_r2_access_key" {
  description = "Donetick R2 access key ID (API token ID)"
  value       = cloudflare_api_token.donetick_r2_access.id
  sensitive   = true
}

output "donetick_r2_secret_key" {
  description = "Donetick R2 secret access key (SHA-256 hash of API token value)"
  value       = sha256(cloudflare_api_token.donetick_r2_access.value)
  sensitive   = true
}

output "donetick_r2_bucket" {
  description = "Donetick R2 bucket name"
  value       = cloudflare_r2_bucket.donetick.name
}

# =============================================================================
# Backups R2 Storage
# =============================================================================

resource "cloudflare_r2_bucket" "backups" {
  account_id = var.cloudflare_account_id
  name       = "nexus-backups"
  location   = "WNAM"  # Western North America
}

resource "cloudflare_api_token" "backups_r2_access" {
  name = "backups-r2-access"

  policies = [{
    permission_groups = [
      { id = one([for p in data.cloudflare_api_token_permission_groups_list.all.result : p.id if p.name == "Workers R2 Storage Bucket Item Read"]) },
      { id = one([for p in data.cloudflare_api_token_permission_groups_list.all.result : p.id if p.name == "Workers R2 Storage Bucket Item Write"]) },
    ]
    resources = jsonencode({
      "com.cloudflare.edge.r2.bucket.${var.cloudflare_account_id}_default_${cloudflare_r2_bucket.backups.name}" = "*"
    })
    effect = "allow"
  }]
}

output "backups_r2_endpoint" {
  description = "R2 S3-compatible endpoint URL for Backups"
  value       = "https://${var.cloudflare_account_id}.r2.cloudflarestorage.com"
  sensitive   = true
}

output "backups_r2_access_key" {
  description = "Backups R2 access key ID (API token ID)"
  value       = cloudflare_api_token.backups_r2_access.id
  sensitive   = true
}

output "backups_r2_secret_key" {
  description = "Backups R2 secret access key (SHA-256 hash of API token value)"
  value       = sha256(cloudflare_api_token.backups_r2_access.value)
  sensitive   = true
}

output "backups_r2_bucket" {
  description = "Backups R2 bucket name"
  value       = cloudflare_r2_bucket.backups.name
}
