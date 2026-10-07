# Virtue <img src="https://github.com/jellyfin/jellyfin-ux/blob/master/branding/SVG/icon-solid-black.svg?raw=true" width="24">

Virtue is a secondary [Jellyfin](https://jellyfin.org/) media server instance running alongside Jellyfin.

Docker Image is from Linuxserver, found [here](https://hub.docker.com/r/linuxserver/jellyfin).

## Setup

Virtue mounts the same media directory as Jellyfin (`${NEXUS_DATA_DIRECTORY}/Media:/data/media`), with its own config directory (`${NEXUS_DATA_DIRECTORY}/Config/virtue:/config`). It is accessed via Traefik at `virtue.${NEXUS_DOMAIN}`.

## Useful Commands

```bash
# View logs
docker logs virtue -f

# Restart
docker restart virtue

# Access shell
docker exec -it virtue sh

# Check stats
docker stats virtue
```
