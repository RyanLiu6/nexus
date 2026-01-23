# DNS Filtering with Cloudflare Zero Trust

DNS-level ad-blocking, malware protection, and content filtering using Cloudflare Gateway.

## How It Works

| Component | Purpose |
|-----------|---------|
| **Cloudflare Gateway** | DNS filtering (ads, malware, phishing, content categories) |
| **Tailscale Split DNS** | Routes `yourdomain.com` to your server |

Gateway filters general DNS queries. Tailscale handles your domain's split DNS. They work independently.

---

## Prerequisites

Update your Cloudflare API token permissions:

1. Go to [Cloudflare API Tokens](https://dash.cloudflare.com/profile/api-tokens)
2. Edit your existing token (or create new)
3. Add permission: **Account → Zero Trust → Edit**

---

## Deploy

```bash
cd terraform
terraform plan    # Preview changes
terraform apply   # Create Gateway resources
```

This creates:
- **DNS Location**: `Tailscale Network` with DoH/DoT endpoints
- **Policy 1**: Block Security Threats (malware, phishing, botnets)
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

---

## Configure Tailscale DNS

After `terraform apply`, get your DoH endpoint:

```bash
terraform output gateway_doh_endpoint
# Returns: https://<location-id>.cloudflare-gateway.com/dns-query
```

You can also find this in the Zero Trust dashboard: **Networks → Resolvers & Proxies** → click your location → DNS over HTTPS.

Then configure Tailscale:

1. Go to [Tailscale DNS Settings](https://login.tailscale.com/admin/dns)
2. Under **Global Nameservers**, click **Add nameserver** → **Custom**
3. Paste your DoH endpoint URL
4. Enable **Override Local DNS**
5. Verify split DNS for your domain is still configured

---

## Verify

From a device connected to Tailscale:

```bash
# Test ad-blocking (should return 0.0.0.0 or NXDOMAIN)
nslookup ads.google.com
nslookup doubleclick.net

# Test your domain still resolves via Tailscale split DNS
dig grafana.yourdomain.com
# Should return your server's Tailscale IP (100.x.x.x)
```

View blocked queries in [Zero Trust Dashboard → Logs → Gateway activity logs](https://one.dash.cloudflare.com/).

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| Split DNS not working | Check Tailscale DNS settings, ensure split DNS entry exists |
| Ads still showing | Verify Gateway policies are active in Zero Trust dashboard |
| Legitimate site blocked | Add to allowlist: Gateway → Lists → Create list → Reference in Allow policy |
| Queries not in logs | Verify DoH endpoint is correctly configured in Tailscale |

### Debug Commands

```bash
# Check Tailscale DNS config
tailscale status --json | jq '.Self'

# Test specific domain
dig @1.1.1.1 ads.example.com  # Compare with
dig ads.example.com            # Your configured DNS
```
