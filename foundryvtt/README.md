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
DATA_DIRECTORY=<your_directory>
```

1. Configure the directory for FoundryVTT to store data. By default, FoundryVTT will mount `$DATA_DIRECTORY/Foundry/data` to `/data` to the container. This behaviour can be configured with the following in `docker-compose.yml`.

```yaml
    - ${DATA_DIRECTORY}/Foundry/data:/data
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

3. Place this file at `$DATA_DIRECTORY/Foundry/data/Config`. This is related to the volume mount specified in `docker-compose.yml`.

### Native Audio and Video Support
Edit `${DATA_DIRECTORY/Foundry/data/Config/options.json` and change `proxySSL: false` to `proxySSL: true`

## Updates
This container will have its image automatically updated via [watchtower](https://ryanliu6/focus/watchtower).

## Backups
Data for Foundry is stored locally at `$DATA_DIRECTORY/Foundry/data`, and can be backed up via cronjob with the following:

```
0 0 * * 4 sudo tar -cf $DATA_DIRECTORY/backups/Foundry/`date +\%F`.tar $DATA_DIRECTORY/Foundry/data
```

> [!NOTE]
> The above directions all assume the default mount location for FoundryVTT's data. If you wish to use your own location, please
> ensure to change the mount location within `docker-compose.yml` as well.
