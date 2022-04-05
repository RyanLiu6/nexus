# ProtonVPN
My setup uses ProtonVPN to secure internet connection. Feel free to use anything.

# Setup
1. Install ProtonVPN-CLI's dependencies with `sudo apt install -y dialog openvpn python3-pip python3-setuptools`.

2. Install ProtonVPN-CLI with `pip install protonvpn-cli`.

3. Initialize ProtonVPN with `sudo protonvpn init`.

   The client will ask you for your OpenVPN username and password. You can find them at https://account.protonvpn.com/account.

   When prompted, choose your plan (mine is Plus). In addition, there will be an option to choose UDP or TCP, choose UDP.

Please find a more detailed setup, along with documentation on commands here: https://github.com/Rafficer/linux-cli-community/blob/master/USAGE.md
