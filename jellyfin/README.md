# Jellyfin

<p align="center">
<img src="../_images/jellyfin.png" alt="jellyfin" title="jellyfin" />
</p>

Jellyfin is a free media server that lets you organize and control your media.

For my purposes, I'll be running an instance of both Plex and Jellyfin to separate types of entertainment, as well as who has access to what services. This is done to separate my personal interests ie Anime, with the interests of my parents, where my server lives.

* [Github](https://github.com/jellyfin/jellyfin)
* [Documentation](https://jellyfin.org/docs/)
* [Docker Image](https://hub.docker.com/r/linuxserver/jellyfin/)

# File Structure
```bash
.
|-- .env
|-- docker-compose.yml
```

- `.env` - a file containing all the environment variables used in the docker-compose.yml
- `docker-compose.yml` - a docker-compose file, use to configure your application’s services
- `cache/` - a directory used to store jellyfin caching data (optionnal)
- `config/` - a directory used to store jellyfin config data
- `media/` - a directory used to store media that will be scanned by jellyfin

Please make sure that all the files and directories are present.

# Setup
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

# Update
The image is automatically updated with [watchtower](../watchtower) thanks to the following label :

```yaml
  # Watchtower Update
  - "com.centurylinklabs.watchtower.enable=true"
```

# Backup
Docker volumes are globally backed up using [borg-backup](../borg-backup).

You may want to exclude the cache and media folder from the backups, add the following to [`borg-backup/excludes.txt`](../borg-backup/excludes.txt):
```
/full/path/to/jellyfin/cache
/full/path/to/jellyfin/media
```
