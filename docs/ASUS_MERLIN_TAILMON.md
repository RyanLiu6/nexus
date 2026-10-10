# Asuswrt-Merlin and TAILMON Setup for Headscale

This guide explains how to install Asuswrt-Merlin on an Asus router, install the TAILMON script, and configure it to connect to your self-hosted Headscale instance (instead of the default Tailscale control servers).

## 1. Prerequisites
*   A compatible Asus Router (check the [Asuswrt-Merlin website](https://asuswrt-merlin.net/) for supported models).
*   A USB Flash Drive (USB 2.0 or 3.0) to hold Entware packages and the Tailscale binary.
*   Your Headscale server URL and an admin user (e.g., `infrastructure`) created on Headscale.

## 2. Installing Asuswrt-Merlin
1.  Download the latest Asuswrt-Merlin firmware for your specific router model from the [official site](https://asuswrt-merlin.net/).
2.  Log into your Asus router's web interface (usually `<YOUR_ROUTER_IP>` or `<YOUR_ROUTER_IP> (e.g., 192.168.x.1)`).
3.  Go to **Administration** -> **Firmware Upgrade**.
4.  Upload the downloaded `.w**` firmware file.
5.  Wait for the router to flash and reboot.

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

## 4. Installing TAILMON
TAILMON is a script that manages Tailscale on Merlin routers.
1.  Still in `amtm`, press `i` to see installable scripts.
2.  Look for **Tailmon** (or run its direct install command if instructed by its GitHub page).
3.  Follow the prompts to download and install TAILMON.

## 5. Configuring TAILMON for Headscale
By default, TAILMON tries to connect to Tailscale's official servers. We need to override this.

### Step 5a: Generate a Headscale Auth Key
On your server hosting Headscale, generate a new authentication key for the `infrastructure` user:
```bash
docker exec -it headscale headscale preauthkeys create --user infrastructure --expiration 24h
```
*(Copy the generated key, it usually starts with `hskey-...`)*

### Step 5b: Configure TAILMON Custom Mode
1.  SSH into your router and type `tailmon` to open the interface.
2.  Press **`K`** to enter the **Configuration Menu**.
3.  Press **`3`** (Set Tailscale Operating Mode), and then select **`3`** again for **Custom** mode.
4.  Back in the Configuration Menu, press **`O`** (Edit Custom Operation Mode Settings).
5.  Press **`4`** to edit the **Commandline Options**.
6.  Enter the following string (replace with your domain and key):
    ```text
    --login-server=https://headscale.yourdomain.com --authkey=YOUR_NEW_KEY
    ```
    *If you want to advertise your home network (Subnet Routing), append `--advertise-routes=<YOUR_LAN_SUBNET> (e.g., 192.168.x.0/24)` to that line.*
7.  Save and exit. TAILMON will restart the Tailscale connection using your Headscale server.

## 6. Subnet Router vs. Exit Node on the Router

If you are using Headscale to manage your infrastructure, you can configure your Asus router to act as a **Subnet Router** or an **Exit Node**.

*   **Subnet Router (`--advertise-routes=<YOUR_LAN_SUBNET> (e.g., 192.168.x.0/24)`)**: This is highly recommended. It bridges your Tailscale network with your physical home network. When you are away from home, you can connect to your NAS, Home Assistant, or other local devices using their normal `<YOUR_LAN_IP>` IP addresses. It does *not* route your normal internet traffic through your home.
*   **Exit Node (`--advertise-exit-node`)**: This routes *all* your internet traffic (web browsing, Netflix, etc.) from your remote device through your home router. It masks your IP to look like you are at home. If you already have a dedicated exit node (like a `tailscale-proton` container), you generally do not need to make your router an exit node as well, but you still want it to be a subnet router.

## 7. Configuring Network Isolation (Main/IoT vs. Guest)

If your home network is configured with:
*   **Main Network (2.4/5/6 GHz):** General usage.
*   **IoT Network (2.4 GHz only):** Shares the same subnet as the Main Network.
*   **Guest Network (2.4/5/6 GHz):** Isolated from the rest of the network.

You can configure TAILMON so that Tailscale bridges with your Main and IoT networks, while completely blocking the Guest network from accessing your Tailnet services.

### A. Exposing the Main & IoT Networks
Because your Main and IoT networks share the same underlying IP subnet (for example, `<YOUR_LAN_SUBNET> (e.g., 192.168.x.0/24)`), enabling access for both is simple.

When configuring TAILMON's custom commandline options (Step 5b), just advertise your main LAN subnet:
```text
--advertise-routes=<YOUR_LAN_SUBNET> (e.g., 192.168.x.0/24)
```
*(Replace `<YOUR_LAN_SUBNET> (e.g., 192.168.x.0/24)` with your router's actual LAN subnet if it is different).*

Because both Main and IoT devices receive IP addresses from this pool, remote Tailnet users will be able to reach devices on both networks seamlessly.

### B. Blocking the Guest Network from the Tailnet
Even though the Guest network is "isolated" (usually via Asus's "Access Intranet: Disable" setting), the router itself handles the Tailscale traffic. To guarantee that devices connected to the Guest Wi-Fi cannot route traffic to your Tailscale network (e.g., trying to access Authentik or your servers at `100.x.y.z`), you must explicitly block their wireless interfaces using `iptables`.

On Asus routers, the first Guest Network on each band is typically assigned the following interfaces:
*   2.4 GHz Guest: `wl0.1`
*   5 GHz Guest: `wl1.1`
*   6 GHz Guest: `wl2.1`

*(Note: If you use Guest Network slot #2, it would be `wl0.2`, `wl1.2`, etc.)*

**To apply the block:**
1.  SSH into your router.
2.  Create or open the firewall start script:
    ```bash
    nano /jffs/scripts/firewall-start
    ```
3.  Add `iptables` drop rules to prevent the guest interfaces from talking to the `tailscale0` interface:
    ```bash
    #!/bin/sh

    # Block 2.4GHz Guest Network from Tailscale
    iptables -I FORWARD -i wl0.1 -o tailscale0 -j DROP

    # Block 5GHz Guest Network from Tailscale
    iptables -I FORWARD -i wl1.1 -o tailscale0 -j DROP

    # Block 6GHz Guest Network from Tailscale
    iptables -I FORWARD -i wl2.1 -o tailscale0 -j DROP
    ```
4.  Make sure the script is executable:
    ```bash
    chmod a+rx /jffs/scripts/firewall-start
    ```
5.  Reboot your router or restart the firewall to apply the changes (`service restart_firewall`).

With this configuration, your Main and IoT networks are fully bridged to your Tailnet, while your Guest network remains securely locked out!
