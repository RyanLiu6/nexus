# Traefik
For my purposes, I'll be using Traefik as my proxy.

# Setup
1. Create and edit permissions to `traefik/acme.json`
```
touch acme.json
chmod 600 acme.json
```

2. Edit `traefik/traefik.yml` with the correct email.

3. Generating hashed password for Traefik: https://medium.com/@techupbusiness/add-basic-authentication-in-docker-compose-files-with-traefik-34c781234970
```
echo $(htpasswd -nbB <USER> "<PASS>") | sed -e s/\\$/\\$\\$/g
```

NOTE: If you're using an environment variable (via .env) like I am, remove the `sed` for string generation.

Alternatively, you can use the script provided in the `traefik` folder - `generate_password.sh`!

4. Create an `.env` file with:
```
MONITOR_DOMAIN=`<traefik domain>`
ADMIN_PASSWORD=<password from step 4 with duplicate $ removed>
```

5. Run it!
```
docker-compose up -d
```
