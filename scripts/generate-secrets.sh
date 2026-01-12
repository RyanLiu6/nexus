#!/bin/bash
# Generate secure passwords for Nexus services

set -e

echo "Generating secure passwords for Nexus..."
echo ""

# Function to generate password hash for Authelia
generate_authelia_hash() {
    local password=$1
    docker run --rm authelia/authelia:latest authelia crypto hash generate argon2 --password "$password"
}

# Function to generate bcrypt hash for Traefik
generate_bcrypt_hash() {
    local password=$1
    # Use openssl to generate bcrypt-like hash (simplified)
    # For production, use htpasswd or similar tool
    openssl passwd -apr1 "$password"
}

# Generate random strings
generate_random() {
    openssl rand -hex 32
}

# Generate passwords
AUTH_JWT_SECRET=$(generate_random)
AUTH_SESSION_SECRET=$(generate_random)
AUTH_STORAGE_KEY=$(generate_random)
ADMIN_PASSWORD=$(generate_random 24)
GAMING_PASSWORD=$(generate_random 24)
WIFE_PASSWORD=$(generate_random 24)
POSTGRES_PASSWORD=$(generate_random 32)
SURE_DB_PASSWORD=$(generate_random 32)
NEXTCLOUD_DB_PASSWORD=$(generate_random 32)
MYSQL_ROOT_PASSWORD=$(generate_random 32)
FOUNDRY_PASSWORD=$(generate_random 24)
FOUNDRY_KEY="CHANGE_ME_your_foundry_license"
TRANSMISSION_PASSWORD=$(generate_random 24)
TRANSMISSION_USERNAME="nexus"
GRAFANA_PASSWORD=$(generate_random 24)

# Generate Authelia password hashes
ADMIN_HASH=$(generate_authelia_hash "$ADMIN_PASSWORD")
GAMING_HASH=$(generate_authelia_hash "$GAMING_PASSWORD")
WIFE_HASH=$(generate_authelia_hash "$WIFE_PASSWORD")

# Generate Traefik password hash
TRAEFIK_HASH=$(generate_bcrypt_hash "$ADMIN_PASSWORD")

# Output vault content
cat > ansible/vars/vault.yml << EOF
---
# Nexus Secrets - Generated on $(date)
# DO NOT commit this file in plaintext!
# Encrypt with: ansible-vault encrypt ansible/vars/vault.yml

# Authelia Configuration
authelia_jwt_secret: "$AUTH_JWT_SECRET"
authelia_session_secret: "$AUTH_SESSION_SECRET"
authelia_storage_encryption_key: "$AUTH_STORAGE_KEY"

# Authelia User Passwords (hashed)
admin_password_hash: "$ADMIN_HASH"
gaming_password_hash: "$GAMING_HASH"
wife_password_hash: "$WIFE_HASH"

# Database Passwords
postgres_password: "$POSTGRES_PASSWORD"
sure_db_password: "$SURE_DB_PASSWORD"
nextcloud_db_password: "$NEXTCLOUD_DB_PASSWORD"
mysql_root_password: "$MYSQL_ROOT_PASSWORD"

# API Tokens
cloudflare_dns_api_token: "CHANGE_ME_your_cloudflare_token"

# Traefik
traefik_user: "admin"
traefik_password_hash: "$TRAEFIK_HASH"

# FoundryVTT
foundry_username: "admin"
foundry_password: "$FOUNDRY_PASSWORD"
foundry_admin_key: "$FOUNDRY_KEY"

# Transmission
transmission_username: "$TRANSMISSION_USERNAME"
transmission_password: "$TRANSMISSION_PASSWORD"

# Nextcloud
mysql_user: "nextcloud"
mysql_database: "nextcloud"

# Sure
sure_postgres_user: "sure_user"
sure_postgres_password: "$SURE_DB_PASSWORD"
sure_postgres_db: "sure_production"
sure_secret_key_base: "$(generate_random 64)"
sure_openai_access_token: ""
sure_port: "5006"

# ACME
acme_email: "your-email@example.com"

# Monitoring
grafana_admin_user: "admin"
grafana_admin_password: "$GRAFANA_PASSWORD"

# Alerting
discord_bot_token: ""
discord_channel_id: ""
discord_webhook_url: ""
alert_provider: "discord"

# Nexus Configuration
nexus_root_directory: "$HOME/dev/focus"
nexus_backup_directory: "$HOME/nexus-backups"
nexus_domain: "ryanliu6.xyz"
tz: "America/Vancouver"
EOF

echo ""
echo "✓ Vault file created: ansible/vars/vault.yml"
echo ""
echo "IMPORTANT: Encrypt the vault file now!"
echo ""
echo "  1. Encrypt vault:"
echo "     ansible-vault encrypt ansible/vars/vault.yml"
echo ""
echo "  2. Save passwords securely:"
echo "     Admin password: $ADMIN_PASSWORD"
echo "     Gaming password: $GAMING_PASSWORD"
echo "     Wife password: $WIFE_PASSWORD"
echo ""
echo "  3. Update Authelia users_database.yml with password hashes"
echo "     admin_password_hash: $ADMIN_HASH"
echo "     gaming_password_hash: $GAMING_HASH"
echo "     wife_password_hash: $WIFE_HASH"
echo ""
echo "  4. Commit encrypted vault to git"
echo "     git add ansible/vars/vault.yml"
echo "     git commit -m 'Add encrypted secrets'"
echo ""
echo "  5. Delete plaintext vault file"
echo "     ansible-vault decrypt ansible/vars/vault.yml > /tmp/vault.yml"
echo "     rm ansible/vars/vault.yml"
echo "     mv /tmp/vault.yml ansible/vars/vault.yml"
echo ""
