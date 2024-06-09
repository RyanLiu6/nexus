# Plex <img src="https://www.plex.tv/wp-content/themes/plex/assets/img/plex-logo.svg" width="32">
[Plex](https://www.plex.tv/) is a Home Media system.

For my own purposes, I've split up media types to use both Plex and Jellyfin to better share media with my family members. Feel free to use one or the other if you don't need to split them!

Docker Image is from Linuxserver, found [here](https://hub.docker.com/r/linuxserver/plex).

## Setup
1. Run it!
```bash
docker-compose up -d
```

2. Configure this server with your plex credentials to connect it.

## Updates
This container will have its image automatically updated via [watchtower](https://ryanliu6/focus/watchtower).

## Backup
There's not much to backup for Plex, since the data that will be backed up will be the actual media to be shared.
