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
> [!NOTE]
> This assumes that `focus` is checked out at `$HOME/dev/focus`!

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

## Updates
This container will have its image automatically updated via [watchtower](https://ryanliu6/focus/watchtower).

If automatic upgrades fail, run the following commands. (More information found [here](https://github.com/nextcloud/docker/issues/1652#issuecomment-986097091))

```bash
1. docker exec -ti nextcloud /bin/bash
2. su - www-data -s /bin/bash -c /var/www/html/occ version
3. apt update && apt install -y vim
4. Update version
5. su - www-data -s /bin/bash -c 'PHP_MEMORY_LIMIT=512M php /var/www/html/occ upgrade'
6. su - www-data -s /bin/bash -c 'PHP_MEMORY_LIMIT=512M php /var/www/html/occ maintenance:mode --off'
```
