# Nexus Secrets Management

This guide covers setting up encrypted secrets management for Nexus using ansible-vault.

## Overview

Nexus uses **ansible-vault** to encrypt sensitive configuration:

- Database passwords
- API keys
- OAuth credentials
- Authelia secrets
- Cloudflare tokens

This allows you to:
- Commit encrypted secrets to git
- Share configuration securely
- Rotate secrets easily
- Avoid accidentally committing plaintext secrets

## Prerequisites

```bash
# Install ansible-vault
uv pip install ansible-vault
```

## Setup

### 1. Create Encrypted Secrets File

```bash
# Create encrypted vault file
ansible-vault create ansible/vars/vault.yml
```

You'll be prompted for a password. **Save this password securely!**

### 2. Add Secrets

Edit the vault file with your sensitive values:

```yaml
---
# Authelia
authelia_jwt_secret: "your-jwt-secret"
authelia_session_secret: "your-session-secret"
authelia_storage_encryption_key: "your-encryption-key"

# Database passwords
postgres_password: "your-postgres-password"
sure_db_password: "your-sure-db-password"
nextcloud_db_password: "your-nextcloud-password"

# API Tokens
cloudflare_dns_api_token: "your-cloudflare-token"

# Service credentials
traefik_user: "admin"
traefik_password_hash: "your-bcrypt-hash"

# OAuth credentials (if using OAuth)
oauth_client_id: "your-client-id"
oauth_client_secret: "your-client-secret"
```

### 3. Encrypt Existing Files

If you have existing secrets in `.env` files, encrypt them:

```bash
# Encrypt entire .env file
ansible-vault encrypt .env
```

## Usage

### Decrypt Secrets

```bash
# View decrypted file
ansible-vault view ansible/vars/vault.yml

# Edit encrypted file
ansible-vault edit ansible/vars/vault.yml

# Decrypt file for temporary use
ansible-vault decrypt ansible/vars/vault.yml --output ansible/vars/vault.decrypted.yml
```

### Use in Ansible

Ansible automatically prompts for vault password:

```bash
# Run playbook with vault
ansible-playbook ansible/playbook.yml

# Or specify password file
ansible-playbook ansible/playbook.yml --vault-password-file ~/.vault_pass.txt
```

### Use in Docker Compose

Docker compose can read environment variables from decrypted files:

```bash
# Decrypt secrets to temporary file
ansible-vault decrypt ansible/vars/vault.yml > /tmp/nexus-secrets.env

# Export variables
set -a && source /tmp/nexus-secrets.env && set +a

# Run docker compose
docker compose up -d

# Clean up
rm /tmp/nexus-secrets.env
```

## Best Practices

### 1. Vault Password Management

```bash
# Store vault password in password manager
# Never commit vault password to git
# Use different password for each environment
```

### 2. Secret Rotation

```bash
# Edit secrets
ansible-vault edit ansible/vars/vault.yml

# Test with new secrets
./scripts/deploy.py -p home

# If working, commit encrypted file
git commit ansible/vars/vault.yml
```

### 3. Multi-Environment Secrets

```bash
# Development
ansible-vault create ansible/vars/vault-dev.yml

# Production
ansible-vault create ansible/vars/vault-vault-prod.yml

# Use specific vault
ansible-playbook playbook.yml --vault-id prod
```

### 4. Sharing Secrets

Team collaboration with ansible-vault:

```bash
# Share encrypted file (safe)
git push origin main

# Team member pulls and decrypts
git pull origin main
ansible-vault view ansible/vars/vault.yml
```

## Security Guidelines

### DO Commit
- ✅ Encrypted vault files (`vault.yml`)
- ✅ Vault structure templates (`.yml.sample`)

### DO NOT Commit
- ❌ Plain text secrets
- ❌ Vault passwords
- ❌ Decrypted files
- ❌ API keys in plaintext

### DO NOT Share
- ❌ Vault password via chat/email
- ❌ Screenshots of decrypted secrets
- ❌ Plaintext in shared documents

### Store Securely
- ✅ Password manager (1Password, Bitwarden)
- ✅ Hardware security key (YubiKey)
- ✅ Encrypted USB drive

## Troubleshooting

### "Vault password incorrect"

**Problem**: Can't decrypt vault file

**Solutions**:
1. Verify vault password with password manager
2. Try decrypting with `ansible-vault view --vault-password-file`
3. If still failing, recreate vault file

### "File already encrypted"

**Problem**: Can't encrypt already encrypted file

**Solutions**:
1. Decrypt first: `ansible-vault decrypt`
2. Make changes
3. Re-encrypt: `ansible-vault encrypt`

### "Vault format invalid"

**Problem**: Ansible can't read vault file

**Solutions**:
1. Check YAML syntax: `ansible-vault view` to verify
2. Ensure file starts with `$ANSIBLE_VAULT`
3. Recreate file if corrupted

### Lost Vault Password

**Problem**: Can't access encrypted secrets

**Solutions**:
1. Re-create vault file from scratch
2. Reset all secrets (generate new passwords)
3. Update all services with new secrets
4. This is a last resort - consider backup plan

## Integration with Nexus Scripts

The Nexus deploy script handles vault automatically:

```bash
# Deploy prompts for vault password automatically
./scripts/deploy.py -p home
```

If you have `~/.vault_pass.txt`, it will use that automatically:

```bash
# Create password file
echo "your-vault-password" > ~/.vault_pass.txt
chmod 600 ~/.vault_pass.txt

# Deploy (no password prompt)
./scripts/deploy.py -p home
```

## Automation

### CI/CD Integration

GitHub Actions example:

```yaml
name: Deploy Nexus
on: [push]
jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Setup Python
        run: pip install ansible-vault
      - name: Decrypt secrets
        env:
          ANSIBLE_VAULT_PASSWORD: ${{ secrets.VAULT_PASSWORD }}
        run: |
          ansible-vault decrypt ansible/vars/vault.yml
```

### Automatic Decryption on Deploy

Add to `~/.bashrc` or `~/.zshrc`:

```bash
# Auto-deploy function
nexus-deploy() {
    cd ~/dev/focus
    ./scripts/deploy.py "$@"
}

# Add to alias
alias nexus=nexus-deploy
```

## Backup Your Secrets

### 1. Vault Password
The password you used to encrypt `ansible/vars/vault.yml` is the "master key". Store it in your Password Manager (1Password, Bitwarden, etc.).

### 2. Terraform State (CRITICAL)
Terraform tracks the infrastructure it created (like DNS records) in a local file: `terraform/terraform.tfstate`.

**If you lose this file:**
- Terraform will not know it already created your DNS records.
- It might try to create duplicates (causing errors) or fail to update existing ones.

**Action:**
- Periodically copy `terraform/terraform.tfstate` to secure storage (e.g., ProtonDrive).
- Do this especially after adding new services or changing domains.

### 3. Encrypted Vault File
The `ansible/vars/vault.yml` file is safe to commit to Git, so your Git host (GitHub/GitLab) acts as a backup for the *content*. You just need the password (Item 1) to read it.

## Resources

- [Ansible Vault Documentation](https://docs.ansible.com/ansible/latest/vault_guide/index.html)
- [Ansible Security Best Practices](https://docs.ansible.com/ansible/latest/user_guide/playbooks_best_practices.html)

## Migration from .env to Vault

```bash
# Step 1: Create vault structure
cp ansible/vars/vault.yml.example ansible/vars/vault.yml

# Step 2: Encrypt it
ansible-vault encrypt ansible/vars/vault.yml

# Step 3: Move secrets from .env to vault
ansible-vault edit ansible/vars/vault.yml
# Add your secrets here

# Step 4: Remove secrets from .env
# Delete sensitive values from .env files

# Step 5: Test
./scripts/deploy.py -p home
```
