# DNS Filtering with Cloudflare Zero Trust

DNS-level ad-blocking, malware protection, and split DNS using Cloudflare Gateway.

## How It Works

```
DNS Query → Cloudflare Gateway
                 │
    ┌────────────┴────────────┐
    │                         │
*.yourdomain.com          Everything else
    │                         │
    ▼                         ▼
Resolve to Tailscale IP   Filter (ads/malware)
(split DNS override)      then resolve normally
```

Gateway handles both:
1. **Split DNS** - Resolves `*.yourdomain.com` to your Tailscale server IP
2. **Content filtering** - Blocks ads, malware, adult content

The apex domain (`yourdomain.com`) is NOT overridden, so Cloudflare Pages still works.

---

## Prerequisites

Update your Cloudflare API token permissions:

1. Go to [Cloudflare API Tokens](https://dash.cloudflare.com/profile/api-tokens)
2. Edit your existing token (or create new)
3. Add permission: **Account → Zero Trust → Edit**

---

## Configuration

Add your server's Tailscale IP to `ansible/vars/vault.yml`:

```yaml
tailscale_server_ip: "100.x.x.x"
```

Find it with: `tailscale ip -4`

Optionally, override Gateway defaults in `terraform/terraform.tfvars.json`:

```json
{
  "enable_gateway": true,
  "gateway_block_ads": true,
  "gateway_block_malware": true,
  "gateway_block_adult_content": true
}
```

---

## Deploy

```bash
inv deploy
# Or just terraform:
cd terraform && terraform apply
```

This creates:
- **DNS Location**: Provides IPv4/DoH endpoints for Tailscale
- **Split DNS Policy**: Resolves `*.yourdomain.com` → your Tailscale IP
- **Block Policies**: Security threats, ads, adult content

---

## Configure Tailscale

After deploy, the summary shows your Gateway DNS IPs:

```
📡 Cloudflare Gateway DNS (optional ad-blocking):
   Add to Tailscale DNS → Global Nameservers:
     Primary: 172.64.36.1
     Backup:  172.64.36.2
```

Configure in Tailscale:

1. Go to [Tailscale DNS Settings](https://login.tailscale.com/admin/dns)
2. Under **Nameservers**, click **Add nameserver**
3. Enter both Gateway IPv4 addresses
4. Enable **Override Local DNS**

No separate split DNS config needed - Gateway handles it.

---

## Verify

```bash
# Test split DNS (should return your Tailscale IP)
nslookup grafana.yourdomain.com
# Expected: 100.x.x.x

# Test ad-blocking (should return 0.0.0.0 or NXDOMAIN)
nslookup ads.google.com

# Test apex domain still works (should return Cloudflare Pages IP)
nslookup yourdomain.com
# Expected: NOT your Tailscale IP
```

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| Subdomains not resolving | Check `tailscale_server_ip` in tfvars, run `terraform apply` |
| Ads still showing | Verify Gateway policies are enabled in Zero Trust dashboard |
| Apex domain broken | Ensure policy only matches `*.domain`, not `domain` itself |

View logs: [Zero Trust → Logs → Gateway activity logs](https://one.dash.cloudflare.com/)
