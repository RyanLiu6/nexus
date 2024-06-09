# Watchtower <img src="https://github.com/containrrr/watchtower/blob/main/logo.png?raw=true" width="24">
[Watchtower](https://containrrr.dev/watchtower/) is a method to automatically and gracefully update the image running for an existing container.

Docker Image is from containrrr, found [here](https://hub.docker.com/r/containrrr/watchtower).

## Setup
1. Setup notifications

For my purposes, I will be using Discord as my method of notification, as this is my personal server. It's not entirely documented within [Watchtower's documentation](https://containrrr.dev/watchtower/notifications/) of notifications, but is explained [here](https://github.com/containrrr/watchtower/discussions/886) in a GitHub discussion thread.

Thus, we will need to create an `.env` file with:
```ini
DISCORD_TOKEN=<some token>
DISCORD_ID=<some id>
```

For other notification methods, please follow the documentation and change both `.env` and `docker-compose.yml` as needed.

> [!NOTE]
> This step is entirely optional, and can be skipped. Simply comment out WATCHTOWER_NOTIFICATIONS_LEVEL, WATCHTOWER_NOTIFICATION_URL, and WATCHTOWER_NOTIFICATION_TEMPLATE under environment for `docker-compose.yml`

2. Run it!
```bash
docker-compose up -d
```

## Updates
This container will have its image automatically updated via [watchtower](https://ryanliu6/focus/watchtower).

## Backup
N/A
