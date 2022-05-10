# FoundryVTT
FoundryVTT is my preferred software for running Virtual Table Top Games.

Courtesy of: https://benprice.dev/posts/fvtt-docker-tutorial/

# Setup
1. Create an `.env` file with:
```
PLAY_DOMAIN=`<foundry domain>`
FOUNDRY_USERNAME=<foundryvtt.com username>
FOUNDRY_PASSWORD=<foundryvtt.com password>
FOUNDRY_ADMIN_KEY=<foundry admin key>
```

2. Run it!
```
docker-compose up -d
```

# Optional config
## AWS S3 Support
1. Create an IAM user on AWS S3 and grant it sufficient permissions to the correct bucket
2. Create `s3.json` with :
```
{
    "accessKeyId": <AWS IAM Access ID>,
    "secretAccessKey": <AWS IAM Secret Access Key>,
    "region": <AWS Bucket Region Codename>
}
```

3. Place this file at `~/Data/foundry/data/Config`. This is related to the volume mount specified in `docker-compose.yml`.

## Native Audio and Video Support
1. Edit `~/Data/foundry/data/Config/options.json` and change `proxySSL: false` to `proxySSL: true`

## Automatic Backup
Create a crontab job and paste in the following:

```
0 2 * * 4 sudo tar -cf /home/<user>/Data/foundry/backups/foundry_`date +\%F`.tar /home/<user>/Data/foundry/data
```

Note: The above cron job creates an archive every Thursday at 2am.
