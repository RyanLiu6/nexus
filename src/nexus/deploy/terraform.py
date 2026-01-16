import json
import logging
import os
import subprocess
import urllib.request
from typing import Any

from nexus.config import TERRAFORM_PATH
from nexus.utils import read_vault


def _get_public_ip() -> str:
    try:
        with urllib.request.urlopen("https://api.ipify.org") as response:
            return str(response.read().decode("utf-8"))
    except Exception as e:
        logging.warning(f"Could not detect public IP: {e}")
        return "127.0.0.1"


def _get_terraform_vars_from_vault(use_tunnel: bool) -> dict[str, str]:
    """Read Cloudflare credentials from vault.yml and return as TF_VAR dict.

    Args:
        use_tunnel: Whether tunnel mode is enabled (requires tunnel_secret).

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
    }

    if use_tunnel:
        key_mapping["tunnel_secret"] = "TF_VAR_tunnel_secret"

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
    use_tunnel: bool = True,
) -> None:
    """Execute Terraform to manage Cloudflare DNS/Tunnel for services.

    For tunnels (recommended): Creates a Cloudflare Tunnel and CNAME records.
    For legacy mode: Creates A records pointing to public IP.

    Reads Cloudflare credentials from vault.yml (decrypted via ansible-vault).

    Args:
        services: List of service names (used for legacy A records).
        domain: Base domain for DNS records (e.g., "example.com").
        dry_run: If True, show plan without applying.
        use_tunnel: If True, use Cloudflare Tunnel. If False, use A records.

    Raises:
        subprocess.CalledProcessError: If terraform init or apply fails.
        ValueError: If required vault values are missing.
    """
    if not (TERRAFORM_PATH / "main.tf").exists():
        logging.warning("Terraform configuration not found. Skipping DNS management.")
        return

    # Get Cloudflare credentials from vault.yml
    logging.info("Reading Cloudflare credentials from vault.yml...")
    tf_env_vars = _get_terraform_vars_from_vault(use_tunnel)

    # Set environment variables for Terraform
    env = os.environ.copy()
    env.update(tf_env_vars)

    # Build non-sensitive tfvars
    tf_vars: dict[str, Any] = {
        "domain": domain,
        "use_tunnel": use_tunnel,
    }

    # Legacy mode needs public IP and subdomains
    if not use_tunnel:
        public_ip = _get_public_ip()
        logging.info(f"Detected Public IP: {public_ip}")
        tf_vars["public_ip"] = public_ip
        tf_vars["subdomains"] = services
        tf_vars["proxied"] = True

    tf_vars_path = TERRAFORM_PATH / "terraform.tfvars.json"

    if dry_run:
        logging.info("[DRY RUN] Configuration:")
        mode = "Cloudflare Tunnel" if use_tunnel else "Port Forwarding"
        logging.info(f"  Mode: {mode}")
        logging.info(f"  Domain: {domain}")
        logging.info(json.dumps(tf_vars, indent=2))
        logging.info("[DRY RUN] Would run: terraform plan")

        # Show plan
        try:
            with open(tf_vars_path, "w") as f:
                json.dump(tf_vars, f, indent=2)
            _run_terraform_cmd(["terraform", "init"], env, capture=True)
            _run_terraform_cmd(["terraform", "plan"], env)
        except subprocess.CalledProcessError:
            logging.warning("Terraform plan failed. Check configuration.")
        return

    mode = "Cloudflare Tunnel" if use_tunnel else "A records"
    logging.info(f"Configuring Cloudflare ({mode}) for {domain}...")

    with open(tf_vars_path, "w") as f:
        json.dump(tf_vars, f, indent=2)

    logging.info("Applying Cloudflare configuration...")
    try:
        _run_terraform_cmd(["terraform", "init"], env, capture=True)
        _run_terraform_cmd(["terraform", "apply", "-auto-approve"], env)

        if use_tunnel:
            logging.info("\n✅ Tunnel created! Next steps:")
            logging.info("   1. Get token: terraform output -raw tunnel_token")
            logging.info("   2. Run: cloudflared tunnel run --token <token>")
        else:
            logging.info("✅ DNS records updated successfully!")
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


def apply_tunnel(dry_run: bool = False) -> None:
    """Apply Cloudflare Tunnel configuration, reading all values from vault.

    This is a convenience function for standalone terraform operations.
    Reads domain and all credentials from vault.yml.

    Args:
        dry_run: If True, show plan without applying.

    Raises:
        ValueError: If required vault values are missing.
    """
    try:
        vault = read_vault()
    except FileNotFoundError as err:
        raise ValueError("vault.yml not found. Run: invoke setup") from err
    except subprocess.CalledProcessError as err:
        raise ValueError(
            "Failed to decrypt vault.yml. Check your vault password."
        ) from err

    domain = vault.get("nexus_domain")
    if not domain or domain == "example.com":
        raise ValueError(
            "nexus_domain not configured in vault.yml.\n"
            "Edit vault.yml: ansible-vault edit ansible/vars/vault.yml"
        )

    run_terraform(services=[], domain=domain, dry_run=dry_run, use_tunnel=True)
