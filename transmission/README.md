# Transmission Bitorrent
For my purposes, I will be using Transmission as my main client.

# Setup
1. Create an `.env` file with
```
TRANSMISSION_USERNAME=<some_username>
TRANSMISSION_PASSWORD=<some_password>
BT_DOMAIN=`<some_domain>`
```

2. Create `${HOME}/Data/transmission` and cp `settings.json` over.

3. Run it!
```
docker-compose up -d
```

4. Make sure to configure some sort of username / password!
