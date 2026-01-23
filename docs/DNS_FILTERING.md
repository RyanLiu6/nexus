# DNS Filtering with Cloudflare Zero Trust

This guide covers setting up DNS-level ad-blocking, malware protection, and content filtering using Cloudflare Zero Trust (Gateway) alongside the existing Tailscale infrastructure.

## Overview

| Component | Purpose |
|-----------|---------|
| **Cloudflare Gateway** | DNS filtering (ads, malware, phishing, content categories) |
| **Tailscale Split DNS** | Routes `yourdomain.com` to your server |
| **Cloudflare Tunnel** | Exposes FoundryVTT publicly |

These work together: Gateway filters general DNS queries while Tailscale handles your domain's split DNS.

---

## Setup Options

There are two ways to set up Cloudflare Gateway:

| Method | Best For |
|--------|----------|
| **Terraform (Automated)** | Existing Nexus deployments, infrastructure-as-code |
| **Manual (Dashboard)** | First-time setup, one-off configurations |

---

## Option A: Terraform (Automated)

If you're already using Nexus's Terraform setup for Cloudflare Tunnel, you can automate Gateway configuration.

### Prerequisites

1. Update your Cloudflare API token permissions:
   - Go to [Cloudflare API Tokens](https://dash.cloudflare.com/profile/api-tokens)
   - Edit your existing token (or create new)
   - Add permission: **Account → Zero Trust → Edit**

2. Ensure your `vault.yml` has the Cloudflare credentials configured

### Deploy Gateway

```bash
# Navigate to terraform directory
cd terraform

# Initialize (if not already done)
terraform init

# Preview changes
terraform plan

# Apply Gateway configuration
terraform apply
```

### What Gets Created

The Terraform configuration (`terraform/cloudflare_gateway.tf`) creates:

- **DNS Location**: `Tailscale Network` - provides unique DNS endpoints
- **Policy 1**: Block Security Threats (malware, phishing, botnets, etc.)
- **Policy 2**: Block Ads & Trackers
- **Policy 3**: Block Adult & Inappropriate Content

### Configuration Variables

Override defaults in `terraform/terraform.tfvars.json`:

```json
{
  "enable_gateway": true,
  "gateway_block_ads": true,
  "gateway_block_malware": true,
  "gateway_block_adult_content": true
}
```

### Get DNS Endpoints

After applying, get your DNS Location endpoints:

```bash
# Get the DoH endpoint
terraform output gateway_doh_endpoint

# Get the location ID (for finding IPs in dashboard)
terraform output gateway_location_id
```

Then find the IPv4/IPv6 addresses in the [Zero Trust Dashboard → Gateway → DNS Locations](https://one.dash.cloudflare.com/).

### Configure Tailscale

Add the Gateway DNS IPs to Tailscale:

1. Go to [Tailscale DNS Settings](https://login.tailscale.com/admin/dns)
2. Add your Gateway IPs as **Global Nameservers**
3. Enable **Override Local DNS**

---

## Option B: Manual Setup (Dashboard)

### Step 1: Create Cloudflare Zero Trust Account

1. Go to [Cloudflare Zero Trust Dashboard](https://one.dash.cloudflare.com/)
2. Sign up or use existing Cloudflare account
3. Create a team name (e.g., `yourname-homelab`)
4. The free plan includes up to 50 users and full Gateway DNS filtering

### Step 2: Create a DNS Location

A DNS Location identifies your network and assigns custom DNS endpoints.

1. Navigate to **Gateway → DNS Locations**
2. Click **Add a location**
3. Configure:
   - **Name**: `Tailscale Network` (or descriptive name)
   - **Source IPv4 Address**: Leave empty (not needed for Tailscale integration)
4. Click **Add location**
5. **Important**: Note the assigned DNS endpoints:
   - **IPv4**: Your unique IPs (e.g., `172.64.36.x`)
   - **IPv6**: Your unique IPv6 addresses
   - **DoH**: `https://<location-id>.cloudflare-gateway.com/dns-query`
   - **DoT**: `<location-id>.cloudflare-gateway.com`

### Step 3: Configure Gateway DNS Policies

Navigate to **Gateway → Firewall Policies → DNS** and create policies in this order (evaluated top to bottom):

#### Policy 1: Block Security Threats

Uses Cloudflare's [recommended security categories](https://developers.cloudflare.com/learning-paths/secure-internet-traffic/build-dns-policies/recommended-dns-policies/).

```
Name: Block Security Threats
Selector: Security Categories
Operator: in
Value: Select ALL of the following:
  - Anonymizer
  - Brand Impersonation (Brand Embedding)
  - Command and Control & Botnet
  - Cryptomining
  - DNS Tunneling
  - Domain Generation Algorithm
  - Malware
  - Phishing
  - Private IP Address
  - Spam
  - Spyware
Action: Block
```

#### Policy 2: Block Ads and Trackers

```
Name: Block Ads & Trackers
Selector: Content Categories
Operator: in
Value:
  - Advertisements
Action: Block
```

#### Policy 3: Block Adult and Inappropriate Content

Based on [domain categories](https://developers.cloudflare.com/cloudflare-one/policies/gateway/domain-categories/).

```
Name: Block Adult & Inappropriate Content
Selector: Content Categories
Operator: in
Value: Select based on your needs:
  - Adult Themes
  - Dating
  - Drugs
  - Gambling
  - Nudity
  - Pornography
Action: Block
```

#### Policy 4: (Optional) Allowlist for False Positives

Create this rule FIRST (top of list) to allow specific domains that get incorrectly blocked:

```
Name: Allowlist
Selector: Domain
Operator: in list
Value: Create a list at Gateway → Lists, then select it
Action: Allow
```

### Step 4: Configure Tailscale to Use Gateway DNS

1. Go to [Tailscale DNS Settings](https://login.tailscale.com/admin/dns)

2. **Global Nameservers** - Add your Gateway DNS Location IPs:
   - Remove any existing nameservers (e.g., NextDNS)
   - Add the IPv4 addresses from Step 2 (your DNS Location)
   - Example: `172.64.36.1`, `172.64.36.2` (use YOUR assigned IPs)

3. **Split DNS** (keep existing):
   - `yourdomain.com` → `100.x.x.x` (your server's Tailscale IP)

4. **Override Local DNS**: **Enable** this to force all Tailscale devices to use Gateway DNS

### Step 5: Verify Configuration

From a device connected to Tailscale:

```bash
# Verify DNS is using Cloudflare (should show Cloudflare)
dig +short whoami.cloudflare CH TXT @1.1.1.1

# Test ad-blocking (should return 0.0.0.0 or NXDOMAIN)
nslookup ads.google.com
nslookup doubleclick.net

# Test malware blocking
nslookup malware.testcategory.com

# Test your domain still resolves via Tailscale split DNS
dig grafana.yourdomain.com
# Should return your server's Tailscale IP (100.x.x.x)
```

---

## Analytics and Logging

Cloudflare Gateway provides comprehensive DNS query logging and analytics.

### Viewing Logs

1. Navigate to **Logs → Gateway → DNS**
2. View real-time and historical DNS queries
3. Each log entry shows:
   - Timestamp
   - Source IP (Tailscale device)
   - Query domain
   - Query type (A, AAAA, CNAME, etc.)
   - Decision (Allowed, Blocked)
   - Categories matched
   - Policy that triggered the action

### Analytics Dashboard

1. Navigate to **Analytics → Gateway**
2. View:
   - **Total queries** over time
   - **Blocked queries** by category
   - **Top blocked domains**
   - **Top allowed domains**
   - **Query types** distribution
   - **Threat categories** breakdown

### Useful Log Filters

| Filter | Purpose |
|--------|---------|
| `Decision: Blocked` | Show only blocked queries |
| `Categories: Malware` | Show malware-related blocks |
| `Categories: Advertisements` | Show ad-related blocks |
| `Resolved IP: 0.0.0.0` | Show sinkholed (blocked) queries |
| `Policy: <name>` | Show queries matching specific policy |

### Setting Up Alerts

1. Navigate to **Notifications → Create**
2. Choose **Gateway DNS**
3. Configure alerts for:
   - High volume of blocked threats
   - New malware detections
   - Specific domain access attempts

---

## DNS Resolution Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                        Your Device                               │
│                     (Tailscale Connected)                        │
└─────────────────────────────────────────────────────────────────┘
                              │
                    DNS Query for domain?
                              │
              ┌───────────────┴───────────────┐
              │                               │
    yourdomain.com?                    Other domains?
              │                               │
              ▼                               ▼
┌─────────────────────────┐     ┌─────────────────────────┐
│   Tailscale Split DNS   │     │   Cloudflare Gateway    │
│                         │     │                         │
│  yourdomain.com         │     │  ✓ Check DNS policies   │
│       ↓                 │     │  ✓ Block if matched     │
│  100.x.x.x (server)     │     │  ✓ Log query            │
│                         │     │  ✓ Return result        │
└─────────────────────────┘     └─────────────────────────┘
```

---

## Comparison: NextDNS vs Cloudflare Gateway

| Feature | NextDNS | Cloudflare Gateway |
|---------|---------|-------------------|
| Ad blocking | ✅ Blocklists | ✅ Content categories |
| Malware protection | ✅ Threat Intelligence | ✅ Security categories |
| Parental controls | ✅ Content categories | ✅ Content categories |
| Analytics/Logs | ✅ 90 days (paid) | ✅ 30 days (free) / longer (paid) |
| Custom blocklists | ✅ Yes | ✅ Yes (Gateway Lists) |
| Allowlists | ✅ Yes | ✅ Yes (Gateway Lists) |
| DoH/DoT | ✅ Yes | ✅ Yes |
| Free tier | 300k queries/mo | 50 users, unlimited queries |

---

## Managing Blocklists and Allowlists

### Creating Custom Lists

1. Navigate to **Gateway → Lists**
2. Click **Create a list**
3. Choose type:
   - **Domain**: Block/allow specific domains
   - **URL**: Block/allow specific URLs
4. Add entries manually or upload CSV

### Using Lists in Policies

Reference your lists in DNS policies:

```
Selector: Domain
Operator: in list
Value: <your-list-name>
Action: Block (or Allow)
```

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| Split DNS not working | Check Tailscale DNS settings, ensure split DNS entry exists |
| Ads still showing | Verify Gateway policies are active, check device is using Gateway DNS |
| Legitimate site blocked | Add domain to allowlist (Gateway → Lists → Add to allowlist) |
| Queries not appearing in logs | Verify DNS Location is configured, check device DNS settings |
| Slow DNS resolution | Try DoH instead of plain DNS for better performance |

### Debug Commands

```bash
# Check current DNS resolver on device
cat /etc/resolv.conf                    # Linux
scutil --dns                            # macOS

# Test if Gateway is your resolver
dig +short txt debug.opendns.com        # Should NOT return OpenDNS

# Test specific domain against Gateway
dig @<your-gateway-ip> ads.example.com

# Check Tailscale DNS config
tailscale status --json | jq '.Self'

# Verify Tailscale is connected
tailscale status
```

---

## Migration Checklist

### Option A: Terraform (Automated)

- [ ] Update Cloudflare API token with Zero Trust:Edit permission
- [ ] Run `terraform init` (if not already initialized)
- [ ] Run `terraform plan` to preview changes
- [ ] Run `terraform apply` to create Gateway resources
- [ ] Note DNS endpoints from `terraform output` or Zero Trust dashboard
- [ ] Configure Tailscale global nameservers (see below)

### Option B: Manual (Dashboard)

- [ ] Create Cloudflare Zero Trust account
- [ ] Create a DNS Location
- [ ] Note your assigned DNS endpoints
- [ ] Create "Block Security Threats" policy
- [ ] Create "Block Ads & Trackers" policy
- [ ] Create "Block Adult & Inappropriate Content" policy
- [ ] (Optional) Create allowlist for false positives

### Tailscale Configuration (Both Options)

- [ ] Go to [Tailscale DNS Settings](https://login.tailscale.com/admin/dns)
- [ ] Remove NextDNS from global nameservers
- [ ] Add Cloudflare Gateway IPs as global nameservers
- [ ] Verify split DNS for your domain is still configured
- [ ] Enable "Override Local DNS"

### Verification

- [ ] Test ad-blocking: `nslookup ads.google.com` (should fail/return 0.0.0.0)
- [ ] Test your homelab domain still resolves via split DNS
- [ ] Verify queries appear in Gateway logs (Zero Trust → Logs → Gateway)
- [ ] Check analytics dashboard shows traffic

### Cleanup

- [ ] Cancel NextDNS subscription (if paid)
- [ ] Remove NextDNS from any other devices/routers
