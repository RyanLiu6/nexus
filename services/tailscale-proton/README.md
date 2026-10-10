# Tailscale-Proton Service

This service runs a Tailscale container configured to act as an exit node (via `--advertise-exit-node`). It connects to the network using a Gluetun container (ProtonVPN) to route traffic through ProtonVPN.

## Associating a Node with a Specific User in Headscale

In Headscale, devices (nodes) belong to specific users. The `tailscale-proton` container is automatically associated with the `infrastructure` user because of the `--authkey` used in its configuration.

### How it works here:
In the `docker-compose.yml`, the environment variable `TS_EXTRA_ARGS` includes `--authkey=hskey-...`. This pre-authentication key was generated on the Headscale server specifically for the `infrastructure` user.

### How to do the same for another device (e.g., your Asus Router):
To associate your Asus router (or any other node) to the `infrastructure` user instead of your personal user:

1. **Generate a new Auth Key for the `infrastructure` user** on your Headscale server:
   ```bash
   # (Run this on the machine hosting your Headscale container)
   docker exec -it headscale headscale preauthkeys create --user infrastructure --reusable --expiration 24h
   ```
2. **Apply the key on your device**:
   * **Standard CLI:** Run `tailscale up --login-server=https://headscale.yourdomain.com --authkey=YOUR_NEW_KEY`
   * **TAILMON (Asus Router):** Go to the Custom Operating Mode configuration and set the commandline options to include the key:
     `--login-server=https://headscale.yourdomain.com --authkey=YOUR_NEW_KEY`

*(Alternatively, you can start `tailscale up` without an auth key. When Tailscale outputs the node key, you can register it manually on the Headscale server by specifying the user: `docker exec -it headscale headscale nodes register --user infrastructure --key <machine_key>`)*.

## Subnet Router vs Exit Node: Should I advertise routes on my router?

You mentioned that you already have this exit node, so you are wondering if you should also "advertise routes" on your Asus router and what it is used for.

### Exit Node (What you have here)
The `tailscale-proton` container is an **Exit Node**. When you use it from your phone or laptop, it funnels **all your internet traffic** through Tailscale, out of this container, and through ProtonVPN to the public internet. It changes your public IP and encrypts your web browsing.

### Advertise Routes / Subnet Router (What your router would do)
"Advertising Routes" turns a device into a **Subnet Router**. It does NOT route your general internet traffic. Instead, it bridges your Tailscale network with your physical home network (LAN).
- **Example:** If your home network uses IPs like `192.168.50.x`, advertising `192.168.50.0/24` from your Asus router allows you to securely access any device on your home network (like smart home hubs, local web interfaces, a NAS, or printers) directly via their local `192.168.50.x` IP address while you are away from home.

**Conclusion:** They serve different purposes, and you can absolutely use both!
- Use your **`tailscale-proton` exit node** when you are on public Wi-Fi and want to encrypt your internet browsing or access geographically restricted content.
- Configure **"Advertise Routes" on your Asus Router** so that when you are traveling, you can still easily connect to local devices running on your home network.
