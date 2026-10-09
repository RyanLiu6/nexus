import io
import os
from pathlib import Path

import yaml
from jinja2 import Environment, FileSystemLoader
from pyinfra import logger
from pyinfra.operations import files, server

# =============================================================================
# Load Secrets
# =============================================================================
SECRETS_PATH = Path("config/secrets.yml")


def load_secrets():
    """Load secrets from the unencrypted YAML file."""
    if not SECRETS_PATH.exists():
        logger.error(f"Secrets file not found at {SECRETS_PATH}")
        return {}
    with open(SECRETS_PATH) as f:
        return yaml.safe_load(f)


secrets = load_secrets()
NEXUS_ROOT = secrets.get("nexus_root_directory", str(Path.cwd()))
NEXUS_DATA = secrets.get("nexus_data_directory", "/Volumes/Data")

logger.info(f"Loaded configuration for {secrets.get('nexus_domain')}")

# =============================================================================
# Determine Services
# =============================================================================
services_str = os.environ.get("NEXUS_SERVICES", "")
if services_str:
    services = [s.strip() for s in services_str.split(",") if s.strip()]
else:
    with open("config/presets.yml") as f:
        presets = yaml.safe_load(f)
    services = presets.get("home", {}).get("services", [])
    services.extend(presets.get("core", []))

logger.info(f"Deploying services: {services}")

# =============================================================================
# Base Directories
# =============================================================================
directories = [
    NEXUS_DATA,
    f"{NEXUS_DATA}/Config",
    f"{NEXUS_DATA}/Config/traefik",
]

for d in directories:
    files.directory(
        name=f"Ensure directory exists: {d}",
        path=d,
        present=True,
    )

# =============================================================================
# Docker Compose Generation
# =============================================================================
all_services_config = {}
all_networks_config = {"proxy": {"external": True}}
all_volumes_config = {}

for svc in services:
    compose_path = Path(f"{NEXUS_ROOT}/services/{svc}/docker-compose.yml")
    if compose_path.exists():
        with open(compose_path) as f:
            content = yaml.safe_load(f)
        if content:
            if "services" in content:
                for k, v in content["services"].items():
                    all_services_config[k] = v
            if "networks" in content:
                for k, v in content["networks"].items():
                    if k != "proxy":
                        all_networks_config[k] = v
            if "volumes" in content:
                for k, v in content["volumes"].items():
                    all_volumes_config[k] = v

final_compose = {
    "services": all_services_config,
    "networks": all_networks_config,
}
if all_volumes_config:
    final_compose["volumes"] = all_volumes_config

compose_content = yaml.dump(final_compose, sort_keys=False, default_flow_style=False)

files.put(
    name="Generate docker-compose.yml",
    src=io.StringIO(compose_content),
    dest=f"{NEXUS_ROOT}/docker-compose.yml",
)

# =============================================================================
# Headscale Config & ACL
# =============================================================================
if "headscale" in services:
    files.directory(
        name="Ensure Headscale config data directories exist",
        path=f"{NEXUS_DATA}/Config/headscale/headplane",
        present=True,
    )

    # Setup Jinja2 environment
    env = Environment(loader=FileSystemLoader("templates"))

    # Render headscale config
    hs_template = env.get_template("headscale-config.yaml.j2")
    hs_config = hs_template.render(
        nexus_domain=secrets.get("nexus_domain"),
        headscale_oidc_client_id=secrets.get("headscale_oidc_client_id", ""),
        headscale_oidc_client_secret=secrets.get("headscale_oidc_client_secret", ""),
        tailscale_users=secrets.get("tailscale_users", {}),
    )
    files.put(
        name="Generate headscale config",
        src=io.StringIO(hs_config),
        dest=f"{NEXUS_DATA}/Config/headscale/config.yaml",
    )

    # Render acl.hujson
    acl_template = env.get_template("acl.hujson.j2")
    acl_config = acl_template.render(tailscale_users=secrets.get("tailscale_users", {}))
    # create tailscale folder first
    files.directory(
        name="Ensure tailscale directory exists",
        path=f"{NEXUS_ROOT}/tailscale",
        present=True,
    )
    files.put(
        name="Generate headscale ACL",
        src=io.StringIO(acl_config),
        dest=f"{NEXUS_ROOT}/tailscale/acl.hujson",
    )


# =============================================================================
# Generate .env file for Docker Compose
# =============================================================================
env_lines = []
for key, value in secrets.items():
    if isinstance(value, str):
        env_key = key.upper()
        env_lines.append(f"{env_key}={value}")

env_lines.append(f"NEXUS_ROOT_DIRECTORY={NEXUS_ROOT}")
env_lines.append(f"NEXUS_DATA_DIRECTORY={NEXUS_DATA}")

files.put(
    name="Generate .env file",
    src=io.StringIO("\n".join(env_lines)),
    dest=f"{NEXUS_ROOT}/.env",
)

# =============================================================================
# Deploy Services
# =============================================================================
server.shell(
    name="Deploy services using docker compose",
    commands=[f"cd {NEXUS_ROOT} && docker compose up -d --remove-orphans"],
)
