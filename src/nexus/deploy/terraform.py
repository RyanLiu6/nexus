import json
import logging
import os
import subprocess
from typing import Any

from nexus.config import TERRAFORM_PATH
from nexus.utils import read_vault


def _get_terraform_vars_from_vault() -> dict[str, str]:
    """Read Cloudflare credentials from vault.yml and return as TF_VAR dict.

    Returns:
        Dictionary of TF_VAR_* environment variables to set.

    Raises:
        ValueError: If required vault keys are missing.
    """
    try:
        vault = read_vault()
    except FileNotFoundError as err:
        raise ValueError(
            "vault.yml not found. "
            "Run: cp ansible/vars/vault.yml.sample ansible/vars/vault.yml"
        ) from err
    except subprocess.CalledProcessError as err:
        raise ValueError(
            "Failed to decrypt vault.yml. Check your vault password."
        ) from err

    # Map vault keys to Terraform variables
    key_mapping = {
        "cloudflare_api_token": "TF_VAR_cloudflare_api_token",
        "cloudflare_zone_id": "TF_VAR_cloudflare_zone_id",
        "cloudflare_account_id": "TF_VAR_cloudflare_account_id",
        "tunnel_secret": "TF_VAR_tunnel_secret",
    }

    # Optional Tailscale API key
    tailscale_api_key = vault.get("tailscale_api_key", "")
    if tailscale_api_key and tailscale_api_key != "CHANGE_ME":
        key_mapping["tailscale_api_key"] = "TF_VAR_tailscale_api_key"

    # Check for missing keys and build env vars
    missing = []
    env_vars = {}

    for vault_key, tf_var in key_mapping.items():
        value = vault.get(vault_key)
        if not value or value == "CHANGE_ME":
            missing.append(vault_key)
        else:
            env_vars[tf_var] = str(value)

    if missing:
        raise ValueError(
            f"Missing or unconfigured values in vault.yml: {', '.join(missing)}\n"
            f"Edit vault.yml: ansible-vault edit ansible/vars/vault.yml"
        )

    return env_vars


def run_terraform(
    services: list[str],
    domain: str,
    dry_run: bool = False,
) -> None:
    """Execute Terraform to manage Cloudflare Tunnel and DNS for services.

    Creates a Cloudflare Tunnel and configures DNS records.
    Reads Cloudflare credentials from vault.yml (decrypted via ansible-vault).

    Args:
        services: List of service names (used for DNS subdomain records).
        domain: Base domain for DNS records (e.g., "example.com").
        dry_run: If True, show plan without applying.

    Raises:
        subprocess.CalledProcessError: If terraform init or apply fails.
        ValueError: If required vault values are missing.
    """
    if not (TERRAFORM_PATH / "main.tf").exists():
        logging.warning("Terraform configuration not found. Skipping DNS management.")
        return

    # Get Cloudflare credentials from vault.yml
    logging.info("Reading Cloudflare credentials from vault.yml...")
    tf_env_vars = _get_terraform_vars_from_vault()

    # Set environment variables for Terraform
    env = os.environ.copy()
    env.update(tf_env_vars)

    # Get optional Tailscale configuration from vault
    tailscale_ip = ""
    tailnet_id = ""
    tailscale_users: dict[str, list[str]] = {}
    try:
        vault = read_vault()
        tailscale_ip = vault.get("tailscale_server_ip", "")
        tailnet_id = vault.get("tailnet_id", "")
        tailscale_users = vault.get("tailscale_users", {})
    except (FileNotFoundError, KeyError, ValueError):
        logging.debug("Could not read Tailscale configuration from vault")
        pass

    # Build subdomains from services
    subdomains = []
    service_map = {
        "dashboard": ["nexus"],
        "monitoring": ["grafana", "prometheus", "alertmanager"],
        "foundryvtt": [],  # Handled by tunnel CNAME
        "tailscale-access": [],  # Internal only
        "vaultwarden": ["vault"],  # Uses 'vault' subdomain
    }

    for svc in services:
        if svc in service_map:
            subdomains.extend(service_map[svc])
        else:
            subdomains.append(svc)

    subdomains = sorted(list(set(subdomains)))

    tf_vars: dict[str, Any] = {
        "domain": domain,
        "tailscale_server_ip": tailscale_ip,
        "tailnet_id": tailnet_id,
        "tailscale_users": tailscale_users,
        "subdomains": subdomains,
    }

    tf_vars_path = TERRAFORM_PATH / "terraform.tfvars.json"

    if dry_run:
        logging.info("[DRY RUN] Configuration:")
        logging.info(f"  Domain: {domain}")
        logging.info(json.dumps(tf_vars, indent=2))
        logging.info("[DRY RUN] Would run: terraform plan")

        try:
            with open(tf_vars_path, "w") as f:
                json.dump(tf_vars, f, indent=2)
            _run_terraform_cmd(["terraform", "init"], env, capture=True)
            _run_terraform_cmd(["terraform", "plan"], env)
        except subprocess.CalledProcessError:
            logging.warning("Terraform plan failed. Check configuration.")
        return

    logging.info(f"Configuring Cloudflare Tunnel for {domain}...")

    with open(tf_vars_path, "w") as f:
        json.dump(tf_vars, f, indent=2)

    logging.info("Applying Cloudflare configuration...")
    try:
        _run_terraform_cmd(["terraform", "init"], env, capture=True)
        _run_terraform_cmd(["terraform", "apply", "-auto-approve"], env)
        logging.info("✅ Tunnel and DNS configured!")
    except subprocess.CalledProcessError:
        logging.error("Terraform failed. Check configuration.")
        raise


def _run_terraform_cmd(
    command: list[str],
    env: dict[str, str],
    capture: bool = False,
) -> subprocess.CompletedProcess[str]:
    logging.debug(f"Running: {' '.join(command)}")
    return subprocess.run(
        command,
        cwd=TERRAFORM_PATH,
        env=env,
        capture_output=capture,
        text=True,
        check=True,
    )


def get_r2_credentials() -> dict[str, str]:
    """Get Foundry R2 credentials from terraform state.

    Returns:
        Dictionary with keys: endpoint, access_key, secret_key, bucket.
        Empty dict if R2 is not provisioned.
    """
    try:
        result = subprocess.run(
            ["terraform", "output", "-json"],
            cwd=TERRAFORM_PATH,
            capture_output=True,
            text=True,
            check=True,
        )
        outputs = json.loads(result.stdout)

        endpoint = outputs.get("foundry_r2_endpoint", {}).get("value", "")
        access_key = outputs.get("foundry_r2_access_key", {}).get("value", "")
        secret_key = outputs.get("foundry_r2_secret_key", {}).get("value", "")
        bucket = outputs.get("foundry_r2_bucket", {}).get("value", "")

        if endpoint and access_key and secret_key and bucket:
            return {
                "endpoint": endpoint,
                "access_key": access_key,
                "secret_key": secret_key,
                "bucket": bucket,
            }
        return {}
    except (
        subprocess.CalledProcessError,
        json.JSONDecodeError,
        KeyError,
        FileNotFoundError,
    ):
        return {}
