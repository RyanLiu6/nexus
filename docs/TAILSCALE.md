# Tailscale Integration

Use [Tailscale](https://tailscale.com) to access your Nexus services securely without exposing ports to the public internet, or to bypass authentication when you are "home" (virtually).

## 1. Setup

### On your Mac Mini (Nexus Server)
1.  **Install:** Download the native macOS app from [tailscale.com/download](https://tailscale.com/download/mac).
2.  **Login:** Sign in with your account.
3.  **Host Name:** Note the machine name (e.g., `nexus-mac-mini`) and IP (e.g., `100.x.y.z`) in the Tailscale admin panel.

### On your Client Devices (Phone, Laptop)
1.  Install the Tailscale app.
2.  Login with the same account.
3.  Enable VPN.

## 2. Authentication Strategy

We configured **Authelia** to trust the Tailscale network range (`100.64.0.0/10`).

**The Experience:**
*   **Public Internet:** Access `https://plex.yourdomain.com` -> Redirected to Authelia Login -> Enter 2FA.
*   **Tailscale VPN:** Access `https://plex.yourdomain.com` -> **Bypasses Authelia** -> Instant access to Plex.

**Important Nuance (Bypass vs. SSO):**
*   **Bypass:** Means Authelia gets out of the way. It does not "log you in" to the application.
*   **Result:**
    *   **Apps with no internal auth (e.g., Radarr, Sonarr):** You get full access immediately.
    *   **Apps with internal auth (e.g., Sure, Nextcloud, Foundry):** You will see the *application's* login screen instead of Authelia's. You still need to log in to the app itself.

## 3. Configuration

### A. Authelia Config
Ensure your `services/auth/configuration.yml` has the `networks` block defined (see `configuration.yml.sample`).

### B. DNS (The "Split Horizon" Trick)
For this to work smoothly, `plex.yourdomain.com` needs to resolve to your server IP.

**Option A: Public DNS (Easiest)**
Point `*.yourdomain.com` to your home's **Public IP**.
*   *Flow:* Phone -> Tailscale -> Internet -> Your Router (Port 443) -> Traefik -> Authelia.
*   *Issue:* Traefik sees your *Public IP* (or Router IP) as the source, NOT the Tailscale IP. **Bypass won't work.**

**Option B: Tailscale DNS (Recommended)**
1.  Go to [Tailscale Admin Console](https://login.tailscale.com/admin/dns).
2.  Add a **Global Nameserver** (e.g., NextDNS or Google).
3.  **Use "Split DNS" / "MagicDNS":**
    *   This is complex to set up for public domains.
    *   **Easier Workaround:** Use `/etc/hosts` on your laptop or "Override" in your specific DNS server to point `*.yourdomain.com` to `100.x.y.z` (Tailscale IP).

### C. Docker on Mac Issue (Warning)
Docker Desktop on Mac runs in a VM. Traffic from the Host (Mac) to a Container often undergoes NAT.
*   **Symptom:** Traefik sees Source IP as `192.168.65.1` (Docker Gateway) instead of `100.x.y.z`.
*   **Result:** Authelia sees the gateway IP, doesn't match `100.64.0.0/10`, and prompts for login.
*   **Fix:**
    *   If this happens, you have to stick to standard Authelia login (it's safer anyway).
    *   Or, use **Tailscale Serve**: `tailscale serve https:443 / http://localhost:443`.

## Summary
For the most consistent experience:
1.  Use Tailscale to access your server securely.
2.  Log in via Authelia once (with "Remember Me" for 30 days).
3.  Don't over-engineer the IP bypass unless you really need it!
