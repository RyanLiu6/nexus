import io
import json
import os
import platform
from pathlib import Path
from typing import Any

import yaml
from jinja2 import Environment, FileSystemLoader
from pyinfra import logger
from pyinfra.operations import files, server

# =============================================================================
# Load Secrets
# =============================================================================
SECRETS_PATH = Path("config/secrets.enc.yml")


def load_secrets():
    """Load secrets, decrypting with SOPS if needed."""
    if not SECRETS_PATH.exists():
        logger.error(f"Secrets file not found at {SECRETS_PATH}")
        return {}

    import subprocess

    try:
        # Try to decrypt with SOPS first
        result = subprocess.run(
            ["sops", "-d", str(SECRETS_PATH)],
            capture_output=True,
            text=True,
            check=True,
        )
        return yaml.safe_load(result.stdout)
    except (subprocess.CalledProcessError, FileNotFoundError):
        # Fall back to reading as plain text if SOPS fails or is not installed
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

    # Generate acl.hujson using native Python dictionaries
    tailscale_users = secrets.get("tailscale_users", {})

    # 1. Build groups
    groups = {}
    for group_name, emails in tailscale_users.items():
        if emails:  # Ensure we don't add empty groups
            groups[f"group:{group_name}"] = emails

    # 2. Build tag owners
    tag_owners = {"tag:nexus-server": ["group:admins"]}

    # 3. Build ACLs
    acls = []

    # Admins get full access to the server
    if "group:admins" in groups:
        acls.append(
            {"action": "accept", "src": ["group:admins"], "dst": ["tag:nexus-server:*"]}
        )

    # Other groups get restricted access (HTTP/HTTPS)
    for group_name in groups.keys():
        if group_name != "group:admins":
            acls.append(
                {
                    "action": "accept",
                    "src": [group_name],
                    "dst": ["tag:nexus-server:80", "tag:nexus-server:443"],
                }
            )

    # Internet access for allowed groups
    internet_srcs = []
    if "group:admins" in groups:
        internet_srcs.append("group:admins")
    if "group:members" in groups:
        internet_srcs.append("group:members")

    if internet_srcs:
        acls.append(
            {"action": "accept", "src": internet_srcs, "dst": ["autogroup:internet:*"]}
        )

    # 4. Build SSH rules
    ssh_rules = []
    if "group:admins" in groups:
        ssh_rules.append(
            {
                "action": "accept",
                "src": ["group:admins"],
                "dst": ["tag:nexus-server"],
                "users": ["autogroup:nonroot", "root"],
            }
        )

    acl_dict = {
        "groups": groups,
        "tagOwners": tag_owners,
        "acls": acls,
        "ssh": ssh_rules,
    }

    acl_config = json.dumps(acl_dict, indent=2)
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
# Override secrets with Terraform environment variables if they are present
tf_vars_mapping = {
    "TF_FOUNDRY_S3_ENDPOINT": "foundry_s3_endpoint",
    "TF_FOUNDRY_S3_ACCESS_KEY": "foundry_s3_access_key",
    "TF_FOUNDRY_S3_SECRET_KEY": "foundry_s3_secret_key",
    "TF_BACKUPS_R2_ENDPOINT": "backups_r2_endpoint",
    "TF_BACKUPS_R2_ACCESS_KEY": "backups_r2_access_key",
    "TF_BACKUPS_R2_SECRET_KEY": "backups_r2_secret_key",
}

for tf_env, secret_key in tf_vars_mapping.items():
    if os.environ.get(tf_env):
        secrets[secret_key] = os.environ[tf_env]

env_lines = []
for key, value in secrets.items():
    if isinstance(value, (str, int, float, bool)):
        env_key = key.upper()
        env_lines.append(f"{env_key}={value}")

# Add explicitly derived paths for compatibility with compose files
userdata_dir = secrets.get("nexus_userdata_directory", f"{NEXUS_DATA}/Config")
env_lines.append(f"FOUNDRYVTT_DATA_DIRECTORY={userdata_dir}/foundryvtt")
env_lines.append(f"PAPERLESS_DOCUMENTS_DIRECTORY={userdata_dir}/paperless")
env_lines.append(f"BOOKORBIT_BOOKS_DIRECTORY={userdata_dir}/bookorbit")

# Map Cloudflare API token for Traefik
env_lines.append(f"CLOUDFLARE_DNS_API_TOKEN={secrets.get('cloudflare_api_token', '')}")

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

# =============================================================================
# ProtonDrive Background Sync
# =============================================================================
protondrive_sync_directory = secrets.get("protondrive_sync_directory", "")
NEXUS_USERDATA = secrets.get("nexus_userdata_directory", "")

if "backups" in services and protondrive_sync_directory:
    is_darwin = platform.system() == "Darwin"
    home = str(Path.home())

    sync_jobs: list[dict[str, Any]] = [
        {
            "id": "com.nexus.protondrive-sync",
            "hour": 4,
            "minute": 0,
            "args": [
                "/bin/bash",
                f"{NEXUS_ROOT}/scripts/sync-to-protondrive.sh",
                f"{NEXUS_DATA}/Backups",
                f"{protondrive_sync_directory}/Containers",
            ],
            "cron_name": "nexus-protondrive-sync",
            "cron_command": (
                f"{NEXUS_ROOT}/scripts/sync-to-protondrive.sh "
                f"{NEXUS_DATA}/Backups {protondrive_sync_directory}/Containers"
            ),
        }
    ]

    if NEXUS_USERDATA:
        sync_jobs.append(
            {
                "id": "com.nexus.protondrive-paperless-sync",
                "hour": 4,
                "minute": 30,
                "args": [
                    "/bin/bash",
                    f"{NEXUS_ROOT}/scripts/sync-to-protondrive.sh",
                    f"{NEXUS_USERDATA}/paperless",
                    f"{protondrive_sync_directory}/paperless",
                    "paperless-web",
                    "paperless-redis",
                    "paperless-db",
                ],
                "cron_name": "nexus-protondrive-paperless-sync",
                "cron_command": (
                    f"{NEXUS_ROOT}/scripts/sync-to-protondrive.sh "
                    f"{NEXUS_USERDATA}/paperless "
                    f"{protondrive_sync_directory}/paperless "
                    f"paperless-web paperless-redis paperless-db"
                ),
            }
        )
        sync_jobs.append(
            {
                "id": "com.nexus.protondrive-bookorbit-sync",
                "hour": 5,
                "minute": 0,
                "args": [
                    "/bin/bash",
                    f"{NEXUS_ROOT}/scripts/sync-to-protondrive.sh",
                    f"{NEXUS_USERDATA}/bookorbit",
                    f"{protondrive_sync_directory}/bookorbit",
                    "bookorbit",
                    "bookorbit-db",
                ],
                "cron_name": "nexus-protondrive-bookorbit-sync",
                "cron_command": (
                    f"{NEXUS_ROOT}/scripts/sync-to-protondrive.sh "
                    f"{NEXUS_USERDATA}/bookorbit "
                    f"{protondrive_sync_directory}/bookorbit "
                    f"bookorbit bookorbit-db"
                ),
            }
        )

    if is_darwin:
        # Create log directory
        files.directory(
            name="Ensure nexus log directory exists",
            path=f"{home}/Library/Logs/nexus",
            present=True,
        )
        for job in sync_jobs:
            plist_path = f"{home}/Library/LaunchAgents/{job['id']}.plist"
            args_xml = "".join(
                f"<string>{arg}</string>\n        " for arg in job["args"]
            )
            plist_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>{job["id"]}</string>
    <key>ProgramArguments</key>
    <array>
        {args_xml.strip()}
    </array>
    <key>StartCalendarInterval</key>
    <dict>
        <key>Hour</key>
        <integer>{job["hour"]}</integer>
        <key>Minute</key>
        <integer>{job["minute"]}</integer>
    </dict>
    <key>RunAtLoad</key>
    <true/>
    <key>StandardOutPath</key>
    <string>{home}/Library/Logs/nexus/{job["id"]}.log</string>
    <key>StandardErrorPath</key>
    <string>{home}/Library/Logs/nexus/{job["id"]}.log</string>
</dict>
</plist>"""

            files.put(
                name=f"Install LaunchAgent: {job['id']}",
                src=io.StringIO(plist_content),
                dest=plist_path,
            )
            server.shell(
                name=f"Load LaunchAgent: {job['id']}",
                commands=[
                    f"launchctl bootout gui/$(id -u) {plist_path} 2>/dev/null || true",
                    f"launchctl bootstrap gui/$(id -u) {plist_path}",
                ],
            )
    else:
        for job in sync_jobs:
            server.crontab(
                name=f"Install crontab: {job['cron_name']}",
                command=job["cron_command"],
                cron_name=job["cron_name"],
                minute=str(job["minute"]),
                hour=str(job["hour"]),
            )
