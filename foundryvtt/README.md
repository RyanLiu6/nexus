# FoundryVTT <img src="https://foundryvtt.com/static/assets/icons/fvtt.png" width="24">
[FoundryVTT](https://foundryvtt.com/) is a powerful software to play role-playing Table Top games online.

Base tutorial came from [here](https://benprice.dev/posts/fvtt-docker-tutorial/)

Docker Image is from felddy, found [here](https://hub.docker.com/r/felddy/foundryvtt).

## Setup
1. Create an `.env` file with:
```ini
PLAY_DOMAIN=`<foundry domain>`
FOUNDRY_USERNAME=<foundryvtt.com username>
FOUNDRY_PASSWORD=<foundryvtt.com password>
FOUNDRY_ADMIN_KEY=<foundry admin key>
```

2. Configure the directory for FoundryVTT to store data. By default, FoundryVTT will mount `$HOME/Data/foundry/data` to `/data` to the container. This behaviour can be configured with the following in `docker-compose.yml`.

```yaml
    - ${HOME}/Data/foundry/data:/data
```

3. Run it!
```bash
docker-compose up -d
```

## Optional config
### AWS S3 Support
1. Create an IAM user on AWS S3 and grant it sufficient permissions to the correct bucket
2. Create `s3.json` with :
```yaml
{
    "accessKeyId": <AWS IAM Access ID>,
    "secretAccessKey": <AWS IAM Secret Access Key>,
    "region": <AWS Bucket Region Codename>
}
```

3. Place this file at `${HOME}/Data/foundry/data/Config`. This is related to the volume mount specified in `docker-compose.yml`.

### Native Audio and Video Support
Edit `${HOME}/Data/foundry/data/Config/options.json` and change `proxySSL: false` to `proxySSL: true`

## Updates
This container will have its image automatically updated via [watchtower](https://ryanliu6/focus/watchtower).

## Backups
Data for Jellyfin is stored locally at `${HOME}/Data/foundry/data`, and can be backed up via cronjob with the following:

```
0 0 * * 4 sudo tar -cf $HOME/Data/foundry/backups/`date +\%F`.tar /home/<user>/Data/foundry/data
```

> [!NOTE]
> The above directions all assume the default mount location for FoundryVTT's data. If you wish to use your own location, please
> ensure to change the mount location within `docker-compose.yml` as well.
