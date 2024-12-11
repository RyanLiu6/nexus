# Focus

Collection of self-hosted services for my personal multi-media home server.

Full credits to [this](https://github.com/BaptisteBdn/docker-selfhosted-apps) repo for introducing watchtower and overall better documentation.

## Services
### Core
* [traefik](traefik/) - reverse proxy and cert manager
* [watchtower](watchtower/) - automatic docker images update

### Content
* [plex](plex/) - media system
* [jellyfin](jellyfin/) - media system
* [nextcloud](nextcloud/) - file storage
* [transmission](transmission/) - torrent client

### Games
* [foundryvtt](foundryvtt/) - [FoundryVTT](https://foundryvtt.com/), a Virtual Table Top for games

### Finance
* [actual](actual/) - local-first personal budgeting tool

### Misc
* [homebridge](homebridge/) - (WIP) SmartHome integration with Apple's HomeKit

## Usage
Each folder has description and usage for individual services, should you wish only do so. Otherwise, an aggregated, "centralized" docker-compose.yml file can be generated via the provided `generate_compose.py` file. Please look at the [Docker](#Docker) section for further details.

If the aggregated approach is taken, we will need to create the proxy network that other containers use first. This can be done with
```bash
docker network create proxy
```

## Docker
Some basic knowledge of Docker and Docker Compose would be good, but not required, as it is fairly easy to pick up and learn. For Docker, please refer to [this](https://docs.docker.com/get-started/overview/) document, and [this](https://docs.docker.com/compose/gettingstarted/) for Docker Compose.

> [!NOTE]
> This guide and individual READMEs assume that your user has been added to the docker group so that all `docker` commands can be ran without the need to use `sudo`. The guide to so can be found [here](https://docs.docker.com/engine/install/linux-postinstall/).

### Compose
The provided `generate_compose.py` script uses my custom Python Library, [Vigor](https://www.github.com/ryanliu6/vigor) to interface with the CLI to generate an aggregated compose file with the correct values from related `.env` files. This is done so that each individual service is self-contained within their own subdirectories and can be run independently of each other. But, the intended usage is to pick and choose which services to run for your servers and only generate a compose file for what is needed.

To be specific, Traefik will always be included in the generated compose file as the absolute core, since its needed to serve traffic. The other core services of Borg and Watchtower are optional and can be included manually.

There's a flag to include everything, `--all`, which will generate a compose file that includes all possible services. Further extension of this flag to generate specific subsets of services is something that can be considered, but with how many services are in consideration now, it is not of much help for the average user.

### Examples
To generate and run for just Plex, Transmission and Nextcloud:
```bash
./generate_compose plex transmission nextcloud
docker compose run -d
```

### Notes
My personal preference is to use images from folks at [linuxserver](https://www.linuxserver.io/). Feel free to change these Docker images to official or any other 3rd party images.

For my own setup, media lives on a separate drive, so I've set the `$DATA_DIRECTORY` environment variable in both `/etc/environment` and `.zshrc`, as this makes the environment variable accessible to both interactive shells and cronjobs. Please take note of this when setting up your own environments!
