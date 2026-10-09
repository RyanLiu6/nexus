# Privacy Policy

**Last Updated:** 2024

This Privacy Policy applies strictly to this private, self-hosted Nexus homelab VPN instance.

## 1. Information Collection and Storage
**We do not store, track, or harvest any personal data.**

We only use Google's OpenID Connect (OIDC) to securely authenticate you into our private network. Your basic profile information (Email Address) is simply passed to our routing software to verify you are an authorized household member.

## 2. Headscale Integration
This private network is powered by **[Headscale](https://headscale.net/)**, an open-source, self-hosted implementation of the Tailscale control server. Headscale natively handles the OIDC authentication handshake directly on our own hardware.

For more information on how the underlying software securely handles authentication and routing without relying on external SaaS providers, please refer to the [official Headscale documentation](https://headscale.net/).

## 3. Third Parties
Because this is an independent homelab, your authentication session is completely localized. It is not shared with, sold to, or accessible by any third parties.
