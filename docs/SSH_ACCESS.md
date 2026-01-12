# SSH Access Documentation

This document covers secure SSH access to your Nexus homelab server, including traditional SSH key management and Tailscale SSH for mobile devices.

## Table of Contents
- [Overview](#overview)
- [Traditional SSH Access](#traditional-ssh-access)
- [Tailscale SSH (Recommended for Mobile)](#tailscale-ssh-recommended-for-mobile)
- [Security Best Practices](#security-best-practices)
- [Troubleshooting](#troubleshooting)

---

## Overview

There are two recommended approaches for SSH access to Nexus:

### Approach 1: Traditional SSH (Desktop/Server Access)
- Use for: Desktop computers, laptops, servers
- Method: SSH key pairs
- Pros: Standard, widely supported, granular control
- Cons: Manual key management, harder on mobile

### Approach 2: Tailscale SSH (Mobile Access - **RECOMMENDED**)
- Use for: Mobile devices (iOS/Android), tablets
- Method: Tailscale built-in SSH with ACLs
- Pros: No key management, works via Tailscale VPN, app-based only
- Cons: Requires Tailscale installation

**Recommendation:** Use Tailscale SSH for mobile devices and traditional SSH for desktops/servers.

---

## Traditional SSH Access

### Prerequisites
- SSH client installed (OpenSSH on Linux/macOS, PuTTY on Windows)
- Admin access to Nexus server

### Method 1: Automated Setup Script

**Quick Setup (Recommended for new devices):**
```bash
# Run from your local machine (NOT the server)
./scripts/setup-ssh.sh user@nexus-server-ip
```

The script will:
1. Generate a new SSH key pair (if needed)
2. Copy public key to server
3. Configure SSH client options
4. Test the connection

### Method 2: Manual Setup

#### Step 1: Generate SSH Key Pair

**On your local machine:**

```bash
# Generate ed25519 key (recommended, most secure)
ssh-keygen -t ed25519 -C "your_email@example.com" -f ~/.ssh/nexus_key

# Or use RSA if ed25519 isn't supported
ssh-keygen -t rsa -b 4096 -C "your_email@example.com" -f ~/.ssh/nexus_key
```

**Prompts:**
- File location: Press Enter to accept default or specify custom path
- Passphrase: Enter a strong passphrase (recommended) or leave empty for key-based auth only

#### Step 2: Copy Public Key to Server

**Option A: Using ssh-copy-id (Linux/macOS):**
```bash
ssh-copy-id -i ~/.ssh/nexus_key.pub user@nexus-server-ip
```

**Option B: Manual copy (Windows or if ssh-copy-id unavailable):**
```bash
# Display public key
cat ~/.ssh/nexus_key.pub

# SSH into server
ssh user@nexus-server-ip

# Add key to authorized_keys
mkdir -p ~/.ssh
echo "YOUR_PUBLIC_KEY_HERE" >> ~/.ssh/authorized_keys
chmod 700 ~/.ssh
chmod 600 ~/.ssh/authorized_keys
```

#### Step 3: Configure SSH Client

**Create/Edit `~/.ssh/config`:**

```ssh
# Nexus Homelab Server
Host nexus
    HostName nexus-server-ip
    User your-username
    IdentityFile ~/.ssh/nexus_key
    PreferredAuthentications publickey
    IdentitiesOnly yes

# Or use Tailscale IP if available
Host nexus-tailscale
    HostName 100.x.y.z
    User your-username
    IdentityFile ~/.ssh/nexus_key
    PreferredAuthentications publickey
    IdentitiesOnly yes
```

#### Step 4: Test Connection

```bash
# Test connection
ssh nexus

# You should be logged in without entering a password
```

### Server-Side SSH Configuration

**On Nexus server:**

**Edit `/etc/ssh/sshd_config`:**

```ssh
# Security hardening
Port 22                          # Or change to non-standard port
Protocol 2
PermitRootLogin no              # Disable root login
PasswordAuthentication no       # Disable password auth (key-only)
PubkeyAuthentication yes        # Enable key auth
PermitEmptyPasswords no

# Rate limiting
MaxAuthTries 3
MaxStartups 10:30:60

# Logging
LogLevel VERBOSE

# Additional security (optional but recommended)
AllowUsers your-username         # Only allow specific users
AllowGroups ssh-users           # Or use groups
```

**Apply changes:**
```bash
# Restart SSH service
sudo systemctl restart sshd         # Linux
sudo brew services restart openssh  # macOS

# Or test config before restarting
sudo sshd -t
```

---

## Tailscale SSH (Recommended for Mobile)

Tailscale SSH eliminates the need to manage SSH keys manually. It uses Tailscale's identity and ACLs for authentication.

### Prerequisites
- Tailscale installed on both server and client devices
- Tailscale admin access (to configure ACLs)

### Method 1: Automated Setup Script

```bash
# Run on Nexus server
sudo ./scripts/setup-tailscale-ssh.sh
```

### Method 2: Manual Setup

#### Step 1: Enable Tailscale SSH on Server

**On Nexus server:**

```bash
# Enable Tailscale SSH
sudo tailscale up --ssh

# Verify SSH is enabled
tailscale status --json | grep ssh
```

This command:
- Installs and configures Tailscale SSH
- Modifies sshd_config to accept Tailscale authentication
- Creates necessary user permissions

#### Step 2: Configure Tailscale ACLs

**Go to:** Tailscale Admin Console → ACLs

**Add SSH access rules:**

```json
{
  "tagOwners": {
    "tag:ssh-admin": ["group:admins"],
    "tag:ssh-user": ["group:users"]
  },
  "acls": [
    {
      "action": "accept",
      "src": ["group:admins"],
      "dst": ["autogroup:internet:*", "tag:ssh-admin:*"]
    },
    {
      "action": "accept",
      "src": ["group:users"],
      "dst": ["autogroup:internet:*", "tag:ssh-user:*"]
    },
    {
      "action": "accept",
      "src": ["*"],
      "dst": ["tag:ssh-admin:*"],
      "approvers": ["group:admins"]
    }
  ],
  "ssh": [
    {
      "action": "check",
      "src": ["*"],
      "dst": ["autogroup:internet:*"],
      "users": ["*"],
      "checkPeriod": "21600h"
    }
  ]
}
```

**Explanation:**
- `tag:ssh-admin`: Admins have full SSH access
- `tag:ssh-user`: Regular users have limited SSH access
- ACLs control who can SSH into which devices

#### Step 3: Assign SSH Tags to Devices

**On Nexus server:**
```bash
# Assign admin SSH tag
sudo tailscale set --tags=tag:ssh-admin
```

**On client devices:**
```bash
# macOS/Linux
sudo tailscale up --ssh

# Windows (admin PowerShell)
tailscale up --ssh
```

### Mobile Access via Tailscale

#### iOS Devices

**Prerequisites:**
- Install [Tailscale iOS app](https://apps.apple.com/app/tailscale/id1474447279)
- Login to your Tailscale account
- Enable Tailscale VPN

**SSH Access Options:**

**Option A: Tailscale iOS App (Built-in)**
1. Open Tailscale app
2. Find your Nexus server in device list
3. Tap on device
4. Select "SSH" or "Terminal"
5. You're now connected!

**Option B: Third-Party SSH App + Tailscale**
1. Install an SSH client app:
   - [Termius](https://apps.apple.com/app/termius-terminal-ssh-client/id549039908)
   - [Blink Shell](https://apps.apple.com/app/blink-shell/id1156707581)
   - [Prompt](https://apps.apple.com/app/prompt/id505921233)
2. Ensure Tailscale VPN is active
3. Use Tailscale IP address (100.x.y.z) or device name:
   ```
   Host: nexus-server-tailscale-name
   Port: 22
   User: your-username
   ```
4. Connect!

**Recommended iOS Setup:**
```bash
# Use Termius for persistent connections
# Add Host:
Host: 100.x.y.z  # Tailscale IP
Port: 22
User: your-username
# No password/key needed - Tailscale handles auth
```

#### Android Devices

**Prerequisites:**
- Install [Tailscale Android app](https://play.google.com/store/apps/details?id=com.tailscale.ipn)
- Login to your Tailscale account
- Enable Tailscale VPN

**SSH Access Options:**

**Option A: Tailscale Android App (Built-in)**
1. Open Tailscale app
2. Find your Nexus server
3. Tap on device
4. Select "SSH"
5. Connection established!

**Option B: Termius (Recommended)**
```bash
# Install Termius from Play Store
# Add Host:
Host: nexus
Address: 100.x.y.z  # Tailscale IP
Port: 22
User: your-username
# Key-based auth not required with Tailscale SSH
```

**Option C: JuiceSSH**
```bash
# Install JuiceSSH from Play Store
# Add Connection:
Nickname: Nexus
Type: SSH
Host: 100.x.y.z
Port: 22
Auth: None (Tailscale handles auth)
Username: your-username
```

### Desktop Access via Tailscale SSH

**macOS/Linux:**
```bash
# SSH using Tailscale device name or IP
ssh your-username@nexus-server-name.tailnet-name.ts.net

# Or use Tailscale IP
ssh your-username@100.x.y.z

# Add to ~/.ssh/config for convenience
Host nexus-ts
    HostName nexus-server-name.tailnet-name.ts.net
    User your-username
    # No IdentityFile needed - Tailscale handles auth
```

**Windows (PowerShell/CMD):**
```powershell
# SSH using Tailscale device name
ssh your-username@nexus-server-name.tailnet-name.ts.net

# Or use Tailscale IP
ssh your-username@100.x.y.z
```

### Benefits of Tailscale SSH

✅ **No SSH keys to manage** - Tailscale handles authentication
✅ **Works over VPN** - Secure connection without exposing ports
✅ **Fine-grained access control** - Use ACLs to control who can access what
✅ **Mobile-friendly** - Built-in support in Tailscale apps
✅ **Automatic revocation** - Remove user from Tailscale = access revoked
✅ **Auditing** - All SSH sessions logged in Tailscale admin console
✅ **Multi-factor** - Can require MFA for SSH access

### Verifying Tailscale SSH Access

**From client device:**
```bash
# Test connection
ssh your-username@nexus-server-name.tailnet-name.ts.net

# Check Tailscale status
tailscale status

# Verify SSH is working
tailscale ping nexus-server-name
```

**From server:**
```bash
# Check active SSH sessions
who

# Check Tailscale connections
tailscale status

# View SSH logs
sudo journalctl -u sshd -f
```

---

## Security Best Practices

### For Traditional SSH

1. **Use strong passphrases** for SSH keys
2. **Disable password authentication** - key-only auth
3. **Change default SSH port** - security through obscurity
4. **Limit users** - only allow necessary users in `sshd_config`
5. **Use fail2ban** - block brute force attempts
6. **Regular key rotation** - update keys every 6-12 months
7. **Backup keys securely** - encrypted password manager
8. **Monitor logs** - check for unauthorized access attempts

### For Tailscale SSH

1. **Restrict ACLs** - only grant necessary access
2. **Use groups** - manage access via user groups
3. **Require MFA** - enable two-factor authentication in Tailscale
4. **Audit regularly** - review Tailscale access logs
5. **Tag devices appropriately** - use different tags for different access levels
6. **Rotate access** - remove users who no longer need access
7. **Use device approval** - require admin approval for new devices

### General Security

1. **Keep SSH updated** - security patches
2. **Use firewall** - block SSH from unknown IPs (except Tailscale)
3. **Backup SSH configs** - in case of server failure
4. **Document access** - keep track of who has access
5. **Regular audits** - review access logs and revokes

---

## Troubleshooting

### Traditional SSH Issues

**Problem: Permission denied (publickey)**
```bash
# Check public key was copied correctly
cat ~/.ssh/authorized_keys

# Verify key permissions on server
chmod 700 ~/.ssh
chmod 600 ~/.ssh/authorized_keys

# Check server logs
sudo tail -f /var/log/auth.log  # Linux
sudo tail -f /var/log/secure    # RHEL/CentOS
```

**Problem: Connection timeout**
```bash
# Check SSH server is running
sudo systemctl status sshd

# Check firewall
sudo ufw status  # Ubuntu
sudo firewall-cmd --list-all  # RHEL/CentOS

# Test connectivity
ping nexus-server-ip
telnet nexus-server-ip 22
```

**Problem: Too many authentication failures**
```bash
# Check if password auth is disabled
cat /etc/ssh/sshd_config | grep PasswordAuthentication

# Enable temporarily for testing (disable after!)
sudo echo "PasswordAuthentication yes" >> /etc/ssh/sshd_config
sudo systemctl restart sshd
```

### Tailscale SSH Issues

**Problem: SSH not working after `tailscale up --ssh`**
```bash
# Check SSH is enabled
tailscale status --json | grep ssh

# Verify sshd_config was modified
sudo grep "tailscale" /etc/ssh/sshd_config

# Restart SSH
sudo systemctl restart sshd
```

**Problem: ACL not allowing access**
```bash
# Check device has correct tags
tailscale status --json | grep tags

# Verify ACL syntax in Tailscale admin console

# Check group membership in Tailscale
```

**Problem: Mobile app can't SSH**
```bash
# Ensure VPN is active on mobile
# Check Tailscale IP is correct
tailscale status

# Try SSH from desktop first to verify Tailscale SSH works
ssh your-username@nexus-server-name.tailnet-name.ts.net
```

**Problem: "Connection refused"**
```bash
# Verify SSH server is running
sudo systemctl status sshd

# Check port is listening
sudo netstat -tlnp | grep :22

# Verify Tailscale is connected
tailscale status
```

### General Troubleshooting

**Enable verbose SSH:**
```bash
ssh -vvv user@server
```

**Check system logs:**
```bash
# Linux
sudo journalctl -xe

# macOS
log show --predicate 'eventMessage contains "ssh"'
```

**Test connectivity:**
```bash
# Ping test
ping server-ip

# Port test
telnet server-ip 22
nc -zv server-ip 22
```

---

## Additional Resources

- [Tailscale SSH Documentation](https://tailscale.com/kb/1193/tailscale-ssh/)
- [OpenSSH Documentation](https://www.openssh.com/manual.html)
- [SSH Key Management Best Practices](https://infosec.mozilla.org/guidelines/openssh)

---

## Quick Reference

### Traditional SSH Commands
```bash
# Generate key
ssh-keygen -t ed25519 -C "email" -f ~/.ssh/nexus_key

# Copy key to server
ssh-copy-id -i ~/.ssh/nexus_key.pub user@server

# Connect
ssh -i ~/.ssh/nexus_key user@server
```

### Tailscale SSH Commands
```bash
# Enable on server
sudo tailscale up --ssh

# Check status
tailscale status --json | grep ssh

# Connect from client
ssh user@server-name.tailnet-name.ts.net
```

### Mobile SSH (iOS)
```bash
# Using Termius
# Host: 100.x.y.z (Tailscale IP)
# User: your-username
# Key: Not needed (Tailscale SSH)
```

### Mobile SSH (Android)
```bash
# Using Termius
# Host: 100.x.y.z (Tailscale IP)
# User: your-username
# Key: Not needed (Tailscale SSH)
```
