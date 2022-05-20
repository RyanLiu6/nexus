# nextcloud

# Setup
1. Create an `.env` file with:
```
CLOUD_DOMAIN=<nextcloud domain>
MYSQL_PASSWORD=<PASSWORD>
MYSQL_DATABASE=nextcloud
MYSQL_USER=nextcloud
MYSQL_ROOT_PASSWORD=<PASSWORD>
```

2. Run it!
```
docker-compose up -d
```

NOTE: This assumes that `focus` is checked out at `$HOME/dev/focus`!

# Backups
1. Nextcloud data is mounted at `$HOME/Data/nextcloud`

2. To back up MySQL
```
# Backup
docker exec CONTAINER /usr/bin/mysqldump -u root --password=<root password> nextcloud > backup.sql

# Restore
cat backup.sql | docker exec -i CONTAINER /usr/bin/mysql -u root --password=<root password> nextcloud
```

# Upgrades
If automatic upgrades fail, run the following commands. (Courtesy of https://github.com/nextcloud/docker/issues/1652#issuecomment-986097091)

```
1. docker exec -ti nextcloud /bin/bash
2. su - www-data -s /bin/bash -c /var/www/html/occ version
3. apt update && apt install -y vim
4. Update version
5. su - www-data -s /bin/bash -c 'PHP_MEMORY_LIMIT=512M php /var/www/html/occ upgrade'
6. su - www-data -s /bin/bash -c 'PHP_MEMORY_LIMIT=512M php /var/www/html/occ maintenance:mode --off'
```
