# Focus

<p align="center">
<img src="_images/moonlight_vigil.png" alt="focus" title="focus" />
</p>


Self-hosted tools and services I have setup for myself at home.

For some of the following services, some config and README files come directly from [this](https://github.com/BaptisteBdn/docker-selfhosted-apps) amazing repo! I've only made minor changes that fits my own personal use-case more.

## Services
### Core
* [traefik](traefik/) - reverse proxy and SSL manager
* [borg-backup](borg-backup/) - backup scripts (local and AWS)
* [watchtower](watchtower/) - automatic docker images update
* [pihole](pihole/) - combination of WireGuard, PiHole, and Unbound

### Content
* [plex](plex/) - media system
* [jellyfin](jellyfin/) - media system, alternative to plex
* [nextcloud](nextcloud/) - file-hosting software system
* [transmission](transmission/) - fast, easy, and free BitTorrent client

### Games
* [foundryvtt](foundryvtt/) - [FoundryVTT](https://foundryvtt.com/), a Virtual Table Top for games
* [gloomhaven](gloomhaven/) - My own copy of Gloomhaven Helper, an assistant to play Gloomhaven

### Misc
* [homebridge](homebridge/) - (WIP) SmartHome integration with Apple's HomeKit

## Usage
Each folder has description and usage for individual services, should you wish only do so.

In order to run things smoothly, a script has been provided `generate_compose.py`. Please look at the [Python Script](#python-script) section for further details.

### Note
One thing to note is that instead of Official Docker Images, I tend to use images packaged by the folks at [linuxserver](https://www.linuxserver.io/). Feel free to change these Docker images to official or any other 3rd party images. I personally prefer linuxserver as their configuration is standarized between all their images, and that is super helpful when added new services here.

## Python Script
This is a custom Python script I wrote to help manage compose and env files. This is specifically helpful as it aggregates compose and `.env`files to generate one main compose and `.env` file each to work with.
