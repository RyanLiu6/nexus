# Traefik <img src="https://upload.wikimedia.org/wikipedia/commons/1/1b/Traefik.logo.png" width="24">
[Traefik](https://doc.traefik.io/traefik/) is an open-source reverse proxy and load balancer.

Docker Image is from traefik, found [here](https://hub.docker.com/r/traefik/traefik).

## Setup
1. Generate a password with `generate_password.sh`

> [!NOTE]
> This step is entirely optional. To skip this step, edit docker-compose.yml and remove the line
> at the bottom that specifies the password

2. Create an `.env` file with:
```ini
DOMAIN=traefik.domain
TLD=com
ACME_EMAIL=your.email@example.com
TRAEFIK_USER=admin
TRAEFIK_PASSWORD_HASH=<password from generate_password.sh>
```

3. Add DNS Provider specific configuration to `.env` and `docker-compose.yml`. In my case, I'm using CloudFlare, and so my file will have the following:
```ini
CLOUDFLARE_DNS_API_TOKEN=<some token>
```

```yaml
  environment:
    - CLOUDFLARE_DNS_API_TOKEN=${CLOUDFLARE_DNS_API_TOKEN}
```

Other DNS Providers will have differing configuration. You can find providers [here](https://doc.traefik.io/traefik/https/acme/#providers) and additional configuration [here](https://go-acme.github.io/lego/dns/).

4. Configure the following directories, as this guide assumes that Focus is cloned to `$HOME/dev/focus`, as that is my own personal preference. This behaviour can be configured with the following in `docker-compose.yml`.

```yaml
  - ${HOME}/dev/focus/traefik/traefik.yml:/traefik.yml:ro
  - ${HOME}/dev/focus/traefik/rules:/rules:ro
  - ${HOME}/dev/focus/traefik/letsencrypt:/letsencrypt
```

5. Run it!
```bash
docker-compose up -d
```

> [!NOTE]
> This assumes that `focus` is checked out at `$HOME/dev/focus`!

## Updates
This container will have its image automatically updated via [watchtower](../watchtower/).

## Backups
N/A
