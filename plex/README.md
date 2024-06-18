# Plex <img src="https://www.plex.tv/wp-content/themes/plex/assets/img/plex-logo.svg" width="32">
[Plex](https://www.plex.tv/) is a Home Media system.

For my own purposes, I've split up media types to use both Plex and Jellyfin to better share media with my family members. Feel free to use one or the other if you don't need to split them!

Docker Image is from Linuxserver, found [here](https://hub.docker.com/r/linuxserver/plex).

## Setup
1. Run it!
```bash
docker-compose up -d
```

2. Configure the media directories to mount so that the container has access to it. By default, Plex will mount `$HOME/Media/anime` to `/anime` to the container. This behaviour can be configured with the following in `docker-compose.yml`.

```yaml
    - ${HOME}/Media/anime:/anime
```

3. Go to `<your-ip>:32400/web`, or if its on a remote server, `<remote-ip>:32400/web` to configure your libraries and claim the Plex server to your Plex account.

## Updates
This container will have its image automatically updated via [watchtower](https://ryanliu6/focus/watchtower).

## Backup
There's not much to backup for Plex, since the data that will be backed up will be the actual media to be shared.
