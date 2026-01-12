# Transmission <img src="https://upload.wikimedia.org/wikipedia/commons/6/6d/Transmission_icon.png" width="24">
[Transmission](https://transmissionbt.com/) is a highly customizable and free BitTorrent client.

Docker Image is from Linuxserver, found [here](https://hub.docker.com/r/linuxserver/transmission).

## Setup
1. Create an `.env` file with:
```ini
TRANSMISSION_USERNAME=<your_username>
TRANSMISSION_PASSWORD=<your_password>
TRANSMISSION_DOMAIN=<your_domain>
DATA_DIRECTORY=<your_directory>
```

2. Ensure that port 51413 is open, on the host and on the router.

For `ufw` (Unix Systems):
```bash
sudo ufw allow 51413
```

For `pf` (MacOS):

Modify `/etc/pf.conf` and add in: `pass in proto tcp from any to any port 51413`. Then, run the following:
```bash
sudo pfctl -f /etc/pf.conf
sudo pfctl -e
sudo pfctl -sr
```

For your router, you'll need to configure that manually as each router will look different!

3. Create `$DATA_DIRECTORY/Config/transmission` and cp `settings.json` over.
> [!NOTE]
> This step is optional since most settings are personalized towards my own needs.
> Feel free to skip this step or modify `settings.json` to your own needs!

4. Configure the directories where Transmission will monitor for new torrent files and where Transmission will download to. By default, Transmission will monitor `$DATA_DIRECTORY/Media/queue` for any torrent files and download to `$DATA_DIRECTORY/Media/complete`, while incomplete files will be saved to `$DATA_DIRECTORY/Media/incomplete`. This behaviour can be configured with the following in `docker-compose.yml`.

```yaml
  - ${DATA_DIRECTORY}/Media:/downloads
  - ${DATA_DIRECTORY}/Media/queue:/watch
```

5. Run it!
```bash
docker-compose up -d
```


## Backup
Data for Transmission is stored locally at `${DATA_DIRECTORY}/Config/transmission`, and can be backed up via cronjob with the following:

```
0 0 * * 4 sudo tar -cf $DATA_DIRECTORY/Backups/transmission/`date +\%F`.tar $DATA_DIRECTORY/Config/transmission
```
