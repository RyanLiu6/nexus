# Transmission <img src="https://upload.wikimedia.org/wikipedia/commons/6/6d/Transmission_icon.png" width="24">
[Transmission](https://transmissionbt.com/) is a highly customizable and free BitTorrent client.

Docker Image is from Linuxserver, found [here](https://hub.docker.com/r/linuxserver/transmission).

## Setup
1. Create an `.env` file with
```ini
TRANSMISSION_USERNAME=<some_username>
TRANSMISSION_PASSWORD=<some_password>
BT_DOMAIN=`<some_domain>`
```

2. Ensure that port 51413 is open, on the host (via `ufw`) and on the router.
For `ufw`:
```bash
sudo ufw allow 51413
```

For your router, you'll need to configure that manually as each router will look different!

3. Create `$HOME/Data/transmission` and cp `settings.json` over.
> [!NOTE]
> This step is optional since most settings are personalized towards my own needs.
> Feel free to skip this step or modify `settings.json` to your own needs!

4. Configure the directories where Transmission will monitor for new torrent files and where Transmission will download to. By default, Transmission will monitor `$HOME/Media/queue` for any torrent files and download to `$HOME/Media/complete`, while incomplete files will be saved to `$HOME/Media/incomplete`. This behaviour can be configured with the following in `docker-compose.yml`.

```yaml
  - ${HOME}/Media:/downloads
  - ${HOME}/Media/queue:/watch
```

5. Run it!
```bash
docker-compose up -d
```

## Updates
This container will have its image automatically updated via [watchtower](https://ryanliu6/focus/watchtower).

## Backup
Data for Transmission is stored locally at `${HOME}/Data/transmission`, and can be backed up via cronjob with the following:

```
0 0 * * 4 sudo tar -cf /home/$USER/Data/transmission/backups/`date +\%F`.tar /home/$USER/Data/transmission
```
