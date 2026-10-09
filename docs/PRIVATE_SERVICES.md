# Nexus Private Services Guide

The Nexus homelab framework supports a "private overlay" mechanism. This allows you to define proprietary, private, or experimental services in a completely separate repository (`nexus-private`) without leaking them into the main public Nexus git repository.

## Overview

The deployment toolchain automatically detects the presence of a private directory and dynamically merges its contents into your homelab deployment at runtime.

Private services benefit from all the same automated features as public services (Tailscale access control, Traefik routing, Homepage dashboard generation) while remaining completely isolated.

### Auto-Detection

The Python deployment scripts (`inv deploy`) look for the private directory in the following order:
1. The path specified by the `NEXUS_PRIVATE_PATH` environment variable.
2. `~/dev/nexus-private` (a sibling directory to the main repository).
3. `~/dev/nexus/.private` (a hidden directory inside the main repository).

*Note: The `.private` and `services/traefik/rules/private` directories are strictly git-ignored in the public repository.*

---

## Structure of `nexus-private`

Your private repository should follow this structure:

```text
nexus-private/
├── config/
│   └── presets.yml      # (Optional) Extends or overrides public presets
├── rules/
│   └── custom.yml       # (Optional) Private Traefik rules (e.g., amane.yml)
└── services/            # (Optional) Private service definitions
    ├── amane/
    │   ├── docker-compose.yml
    │   └── service.yml
    └── my-secret-app/
        ├── docker-compose.yml
        └── service.yml
```

### 1. Services (`services/`)

To add a new private service, simply create a folder under `services/` exactly as you would in the public repo.

**Example `services/my-secret-app/service.yml`:**
```yaml
name: my-secret-app
description: "A completely private application"
category: "Media"
url: "https://secret.{{ domain }}"
icon: "mdi-lock"
subdomains:
  - "secret"
```

**Example `services/my-secret-app/docker-compose.yml`:**
```yaml
services:
  my-secret-app:
    image: my-private-image:latest
    container_name: my-secret-app
    restart: unless-stopped
    networks:
      - nexus
    labels:
      - traefik.enable=true
      - traefik.docker.network=nexus
      - traefik.http.routers.my-secret-app.rule=Host(`secret.${NEXUS_DOMAIN}`)
      - traefik.http.routers.my-secret-app.entrypoints=https
      - traefik.http.routers.my-secret-app.middlewares=tailscale-chain@file
      - traefik.http.routers.my-secret-app.tls=true
      - traefik.http.routers.my-secret-app.tls.certresolver=certchallenge
```

### 2. Presets (`config/presets.yml`)

You can define entirely new presets or extend existing public presets (like `home`) to include your private services.

**Example `config/presets.yml`:**
```yaml
# Append private services to the public 'home' preset
home:
  extends: home
  services:
    - my-secret-app
    - amane

# Create a completely new preset
secret-preset:
  - traefik
  - tailscale-access
  - my-secret-app
```

### 3. Traefik Rules (`rules/`)

Any `*.yml` files placed in `rules/` are automatically copied to the main repository's `services/traefik/rules/private/` directory during `inv deploy`. Traefik immediately reads these files and applies the routing configurations.

This is extremely useful for routing non-docker services or setting up custom middleware chains specifically for your private apps.

---

## How it Works Under the Hood

When you run `inv deploy`:

1. **Manifest Discovery**: `src/nexus/services.py` scans `nexus/services/` AND `nexus-private/services/`. It compiles a master dictionary of all `service.yml` manifests.
2. **Preset Merging**: `src/nexus/config.py` loads the public `presets.yml` and then intelligently merges any configurations found in the private `presets.yml`.
3. **Ansible Generation**: The Ansible playbook takes the merged preset list. It loops through both the public and private service directories, appending every matching `docker-compose.yml` fragment into the single, massive `docker-compose.yml` placed in the Nexus root.
4. **Dashboard Links**: The homepage generator scans the private `service.yml` manifests and `rules/` files, dynamically generating dashboard links for your private apps without committing those links to the public repo.

## Adding a New Service (Quickstart)

1. Create the service directory: `mkdir -p ~/dev/nexus-private/services/new-app`
2. Create `service.yml` defining the app's metadata (URL, subdomains, icon).
3. Create `docker-compose.yml` for the container setup.
4. Add `new-app` to `~/dev/nexus-private/config/presets.yml` under the `home` preset extension.
5. Deploy normally: `inv deploy --preset home`
