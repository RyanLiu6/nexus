# Jellyfin <img src="https://github.com/jellyfin/jellyfin-ux/blob/master/branding/SVG/icon-solid-black.svg?raw=true" width="24">
[Jellyfin](https://jellyfin.org/) is a Home Media system.

For my own purposes, I've split up media types to use both Plex and Jellyfin to better share media with my family members. Feel free to use one or the other if you don't need to split them!

Docker Image is from Linuxserver, found [here](https://hub.docker.com/r/linuxserver/jellyfin).

## Setup
1. Create an `.env` file with:
```ini
JELLYFIN_DOMAIN=`<jellyfin domain>`
```

2. Modify compose file to specify your media location. The default volume mounting is:
```yaml
- ${HOME}/Media/config/jellyfin:/config
- ${HOME}/Media/movies:/data/movies
```

3. Run it!
```
docker compose up -d
```

## Updates
This container will have its image automatically updated via [watchtower](https://ryanliu6/focus/watchtower).

## Backups
There's not much to backup for Jellyfin, since the data that will be backed up will be the actual media to be shared.

If you so wish, config can be backed up and preserved; its stored locally at `${HOME}/Media/config/jellyfin`, and can be backed up via cronjob with the following:

```
0 0 * * 1 sudo tar -cf $HOME/Data/jellyfin/backups/`date+%F`.tar /home/<user>/Media/config/jellyfin
```
