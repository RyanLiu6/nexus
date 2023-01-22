# Traefik

<p align="center">
<img src="../_images/traefik.png" alt="traefik" title="traefik" />
</p>

Traefik is an excellent alternative choice to Nginx when it comes to being an HTTP reverse proxy and load balancer that works smoothly with Docker. Its built around the idea of deploying microservices, and works perfectly for my purposes.

* [Github](https://github.com/traefik/traefik/)
* [Documentation](https://doc.traefik.io/traefik/)
* [Docker Image](https://hub.docker.com/_/traefik)

# File Structure
```bash
.
|-- .env
|-- docker-compose.yml
|-- letsencrypt/
|-- rules/
|   |-- tls.yml
|   |-- whitelist.yml
|-- traefik.yml
```

- `.env` - a file containing all the environment variables used in the docker-compose.yml
- `docker-compose.yml` - a docker-compose file, use to configure your application’s services
- `letsencrypt/` - a directory used to store the certificates' information
- `rules/` - a directory used to store traefik optional rules (TLS, IP whitelist)
- `traefik.yml` - traefik configuration file

Please make sure that all the files and directories are present.

## socket-proxy
The socket-proxy service is used to protect the docker socket, allowing Traefik unrestricted access to your Docker socket file could result in a vulnerability to the host computer, as per [Traefik own documentation](https://doc.traefik.io/traefik/providers/docker/#docker-api-access), should any other part of the Traefik container ever be compromised.

Instead of allowing Traefik container full access to the Docker socket file, we can instead proxy only the API calls we need with [Tecnativa’s Docker Socket Proxy](https://github.com/Tecnativa/docker-socket-proxy), following the [principle of the least privilege](https://en.wikipedia.org/wiki/Principle_of_least_privilege).

## traefik
### DNS Challenge with Let's Encrypt
Traefik can use an ACME provider (like Let's Encrypt) for automatic certificate generation. It will create the certificate and attempt to renew it automatically 30 days before expiration. One of the great benefit of using DNS challenges is that it will allow us to use wildcard certificates, on the other hand, it can create a security risk as it requires giving rights to Traefik to create and remove some DNS records.

For the DNS challenge, you'll need a [working provider](https://doc.traefik.io/traefik/https/acme/#providers) along with the credentials allowing to create and remove DNS records,
If you are using OVH, you can use this [guide](https://medium.com/nephely/configure-traefik-for-the-dns-01-challenge-with-ovh-as-dns-provider-c737670c0434) to retrieve the credentials.

### Global redirect to HTTPS
```yaml
      # global redirect to https
      - "traefik.http.routers.http-catchall.rule=hostregexp(`{host:.+}`)"
      - "traefik.http.routers.http-catchall.entrypoints=http"
      - "traefik.http.routers.http-catchall.middlewares=redirect-to-https"
```
This rule will match all the HTTP requests and redirect them to HTTPS. It uses the redirect-to-https middleware.

### Redirect root to www
```yaml
      # redirect root to www
      - "traefik.http.routers.root.rule=host(`example.com`)"
      - "traefik.http.routers.root.entrypoints=https"
      - "traefik.http.routers.root.middlewares=redirect-root-to-www"
      - "traefik.http.routers.root.tls=true"
```
This rule will automatically redirect the root domain `example.com` to `www.example.com`.

# Setup
## Requirements
- A domain, we will use example.com for this guide.
- DNS manager, usually it goes with the provider you used for your domain. List of compatible [providers](https://doc.traefik.io/traefik/https/acme/#providers).
- Ports 80 and 443 open, check your firewall.

1. Generate a hashed password for Traefik: https://medium.com/@techupbusiness/add-basic-authentication-in-docker-compose-files-with-traefik-34c781234970
```
echo $(htpasswd -nbB <USER> "<PASS>") | sed -e s/\\$/\\$\\$/g
```

<!-- NOTE: If you're using an environment variable (via .env) like I am, remove the `sed` for string generation. -->

2. Create an `.env` file with:
```
MONITOR_DOMAIN=`<traefik domain>`
ADMIN_PASSWORD=<password from step 4 with duplicate $ removed>
DOMAIN=`<root domain>`
TLD=`<tld>
```

3. Update `traefik.yml` to have your actual email address
```
certificatesResolvers:
  mydnschallenge:
    acme:
      email: mail@example.com -> Your actual email address
```

4. Create proxy network
```
docker network create proxy
```

5. (Optional) Update whitelist
Replace the IP address in `rules/whitelist.yml`. Use the IP address as well as the [CIDR](https://en.wikipedia.org/wiki/Classless_Inter-Domain_Routing). Whitelist is disable by default with `0.0.0.0/0`. The whitelist will be used on containers setting the following label. <br>
  ```yaml
    # Ip filtering
    - "traefik.http.routers.service-router-name.middlewares=whitelist@file"
  ```
  You can use the private IP address range used by docker (172.16.0.0/12) if you are using [wireguard](../pihole). Then your services will only be available through your VPN (recommend for a better security).

6. Run it!
```
docker compose up -d
```

## Note
If you want to use the [Redirect root to www](#redirect-root-to-www) fonctionnality, you also need to have a certificate generated for your root domain. In order to do so, you will need to use a service which uses the root domain.

# Update
Both `traefik` and `socket-proxy` images are automatically updated with [watchtower](../watchtower) thanks to the following label :

```yaml
  # Watchtower Update
  - "com.centurylinklabs.watchtower.enable=true"
```

# Security
The socket-proxy service is used to protect the docker socket.

# Backup
Docker volumes are globally backed up using [borg-backup](../borg-backup).
