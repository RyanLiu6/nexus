# NextCloud <img src="https://upload.wikimedia.org/wikipedia/commons/6/60/Nextcloud_Logo.svg" width="32">
[NextCloud](https://nextcloud.com/) is an open-source alternative to the many offerings that Google provides, mainly for storage and collaboration.

Docker Image is from Linuxserver, found [here](https://hub.docker.com/r/linuxserver/nextcloud).

## Setup
1. Create an `.env` file with:
```ini
CLOUD_DOMAIN=<nextcloud domain>
MYSQL_PASSWORD=<PASSWORD>
MYSQL_DATABASE=nextcloud
MYSQL_USER=nextcloud
MYSQL_ROOT_PASSWORD=<PASSWORD>
```

2. Run it!
```bash
docker-compose up -d
```

## Backups
Data for NextCloud is stored locally at `$HOME/Data/nextcloud`, and can be backed up with the following:

```bash
# Backup
docker exec CONTAINER /usr/bin/mysqldump -u root --password=<root password> nextcloud > backup.sql

# Restore
cat backup.sql | docker exec -i CONTAINER /usr/bin/mysql -u root --password=<root password> nextcloud
```

> [!NOTE]
> A cronjob specification is not provided here as I personally no longer use NextCloud as I used to. Feel free to
> copy configuration from other services in this repo for a period cronjob.

