# Asuswrt-Merlin and TAILMON Setup for Headscale

This guide explains how to install Asuswrt-Merlin on an Asus router, install and configure the TAILMON script to connect to a self-hosted Headscale instance in high-performance **Kernel Mode**, configure Subnet Routing with network isolation, and set up passwordless SSH access.

---

## 1. Prerequisites
*   A compatible Asus Router (check the [Asuswrt-Merlin website](https://asuswrt-merlin.net/) for supported models).
*   A USB Flash Drive (USB 2.0 or 3.0) to hold Entware packages and the Tailscale binary.
*   Your Headscale server URL and a user created on Headscale (e.g., `Infrastructure`).

---

## 2. Installing Asuswrt-Merlin
1.  Download the latest Asuswrt-Merlin firmware for your specific router model from the [official site](https://asuswrt-merlin.net/).
2.  Log into your Asus router's web interface (usually `<YOUR_ROUTER_IP>` or `<YOUR_ROUTER_IP> (e.g., 192.168.x.1)`).
3.  Go to **Administration** -> **Firmware Upgrade**.
4.  Upload the downloaded `.w**` firmware file.
5.  Wait for the router to flash and reboot.

---

## 3. Preparing the USB Drive (AMTM and Entware)
Tailscale is too large to fit in the router's internal NVRAM/JFFS storage, so it must be installed on a USB drive.

1.  Plug your USB drive into the router.
2.  Enable SSH on your router: Go to **Administration** -> **System**, set **Enable SSH** to `LAN only`.
3.  SSH into your router: `ssh admin@<YOUR_ROUTER_IP> (e.g., 192.168.x.1)` (replace with your router's IP and username).
4.  Launch the Asuswrt-Merlin Terminal Menu (AMTM) by typing:
    ```bash
    amtm
    ```
5.  Format the USB drive: Press `fd` in AMTM and follow the prompts to format it as `ext4` (this will erase the drive).
6.  Install Entware: Once formatted, press `ep` in AMTM to install Entware to the USB drive.

---

## 4. Installing TAILMON
TAILMON is an Asuswrt-Merlin script that automates and monitors Tailscale.
1.  Still in `amtm`, press `i` to see installable scripts.
2.  Look for **Tailmon** (or run its direct install command if instructed by its GitHub page).
3.  Follow the prompts to download and install TAILMON.

---

## 5. Critical Pre-Configuration

### Step 5a: Fix Router NAT Loopback (Split DNS)
> [!IMPORTANT]
> If your Headscale server runs on a host **inside your local home network**, you **must** configure Split DNS on the router.
> Without this, the router tries to connect to its own external WAN IP on port 443. Linux NAT loopback (hairpinning) does not apply to processes originating from the router itself, causing the Tailscale handshake to hang indefinitely.

Run these commands on your router:
```bash
# Point the headscale domain directly to your internal server's LAN IP
echo "<YOUR_SERVER_LAN_IP> headscale.yourdomain.com" >> /jffs/configs/hosts.add

# Restart dnsmasq to apply
service restart_dnsmasq

# Verify it resolves to your LAN IP immediately
ping -c 2 headscale.yourdomain.com
```

### Step 5b: Generate a Headscale Auth Key
On your host server running Headscale, find the User ID for your infrastructure user:
```bash
docker exec headscale headscale users list
```
Then generate a long-lived reusable key (e.g., 10 years / 87,600 hours):
```bash
docker exec headscale headscale preauthkeys create -u <USER_ID> --reusable --expiration 87600h
```
*(Copy the generated key, which starts with `hskey-auth-...`)*.

---

## 6. Configuring TAILMON (Kernel Mode + Custom Headscale Login)

TAILMON has presets for "Userspace" and "Kernel", but both presets default to commercial Tailscale servers. To get both **high-performance Kernel Mode** (using `modprobe tun`) and your **custom Headscale login**, use TAILMON's **Custom Mode**.

### Method 1: Direct CLI Login & Config (Fastest)

1. Ensure the background daemon is running:
   ```bash
   /opt/etc/init.d/S06tailscaled start
   ```

2. Perform the initial authentication:
   ```bash
   tailscale up --login-server=https://headscale.yourdomain.com --authkey=YOUR_NEW_KEY --advertise-routes=<YOUR_LAN_SUBNET> (e.g., 192.168.x.0/24) --reset
   ```

3. Persist Kernel Mode and Custom parameters in `/jffs/addons/tailmon.d/tailmon.cfg`:
   ```bash
   nano /jffs/addons/tailmon.d/tailmon.cfg
   ```
   Ensure these settings are present:
   ```sh
   tsoperatingmode="Custom"
   precmd="modprobe tun"
   args="--state=/opt/var/tailscaled.state --statedir=/opt/var/lib/tailscale"
   preargs="nohup"
   customcmdline="--login-server=https://headscale.yourdomain.com --advertise-routes=<YOUR_LAN_SUBNET> (e.g., 192.168.x.0/24)"
   ```
   *(Save with `Ctrl+O`, exit with `Ctrl+X`)*.

### Method 2: Via the TAILMON Menu

1. Run `tailmon` in your router terminal.
2. Press **`K`** (Configuration Menu) -> Press **`3`** (Set Operating Mode) -> Select **`3`** (Custom).
3. Press **`O`** (Edit Custom Settings):
   * Option 1 (**ARGS**): Set to `--state=/opt/var/tailscaled.state --statedir=/opt/var/lib/tailscale`
   * Option 3 (**PRECMD**): Set to `modprobe tun`
   * Option 4 (**Commandline Options**): Set to `--login-server=https://headscale.yourdomain.com --advertise-routes=<YOUR_LAN_SUBNET> (e.g., 192.168.x.0/24)`
4. Save and return to the main menu.

---

## 7. Headscale Approvals & ACL Permissions

### Step 7a: Approve the Subnet Route
In Headscale, advertised subnet routes are not active until an administrator approves them.

On your Headscale server:
```bash
# 1. Check the node ID and available routes
docker exec headscale headscale nodes list-routes

# 2. Approve the advertised route (replace <NODE_ID> and subnet)
docker exec headscale headscale nodes approve-routes -i <NODE_ID> -r <YOUR_LAN_SUBNET> (e.g., 192.168.x.0/24)
```

### Step 7b: Ensure ACLs Permit Admin Access
In `tailscale/acl.hujson` (and `infra.py`), ensure your admin group has access to everything (`*:*`) so your laptops and devices can communicate with the router and subnet routes:
```json
{
  "acls": [
    {
      "action": "accept",
      "src": [
        "group:admins"
      ],
      "dst": [
        "*:*"
      ]
    }
  ]
}
```

---

## 8. Network Isolation (Main/IoT vs. Guest)

If your router serves:
*   **Main Network (2.4/5/6 GHz):** General usage.
*   **IoT Network (2.4 GHz only):** Shares the same subnet as the Main Network.
*   **Guest Network (2.4/5/6 GHz):** Isolated from the rest of the network.

### Exposing Main & IoT
Because Main and IoT share `<YOUR_LAN_SUBNET> (e.g., 192.168.x.0/24)`, advertising that single subnet allows remote Tailscale users to reach devices on both networks.

### Blocking the Guest Network
To ensure Guest devices cannot access your Tailscale network (e.g., internal services at `100.x.y.z`), add `iptables` drop rules for the Guest Wi-Fi interfaces in `/jffs/scripts/firewall-start`:

1. Edit the firewall script:
   ```bash
   nano /jffs/scripts/firewall-start
   ```
2. Add drop rules:
   ```bash
   #!/bin/sh

   # Block Guest Network interfaces from reaching Tailscale
   iptables -I FORWARD -i wl0.1 -o tailscale0 -j DROP  # 2.4 GHz Guest
   iptables -I FORWARD -i wl1.1 -o tailscale0 -j DROP  # 5 GHz Guest
   iptables -I FORWARD -i wl2.1 -o tailscale0 -j DROP  # 6 GHz Guest
   ```
3. Make the script executable:
   ```bash
   chmod a+rx /jffs/scripts/firewall-start
   service restart_firewall
   ```

---

## 9. Passwordless SSH Access

To SSH into your router from your laptop without entering a password:

### Option A: `ssh-copy-id`
From your MacBook/laptop terminal:
```bash
ssh-copy-id <ROUTER_USER>@<ROUTER_TAILSCALE_IP>
```

### Option B: Asus Web GUI
1. On your laptop, copy your public key:
   ```bash
   cat ~/.ssh/id_ed25519.pub | pbcopy
   ```
2. In the Asus web GUI, go to **Administration** -> **System** -> **SSH Daemon**.
3. Paste the key into the **Authorized Keys** text box and click **Apply**.

### Connecting
You can now connect securely from anywhere via your router's Tailscale IP or MagicDNS:
```bash
ssh <ROUTER_USER>@<ROUTER_TAILSCALE_IP>
# or
ssh <ROUTER_USER>@<ROUTER_NAME>.nexus.internal
```
