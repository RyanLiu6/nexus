import json
import logging
import subprocess
import urllib.request

from nexus.config import TERRAFORM_PATH
from nexus.utils import run_command


def _get_public_ip() -> str:
    try:
        with urllib.request.urlopen("https://api.ipify.org") as response:
            return str(response.read().decode("utf-8"))
    except Exception as e:
        logging.warning(f"Could not detect public IP: {e}")
        return "127.0.0.1"


def run_terraform(services: list[str], domain: str, dry_run: bool = False) -> None:
    """Execute Terraform to manage Cloudflare DNS records for services.

    Generates a terraform.tfvars.json file with the current public IP and
    service subdomains, then runs terraform init and apply to update DNS.

    Args:
        services: List of service names to create DNS A records for.
            Each service gets a subdomain (e.g., "plex" -> "plex.domain.com").
        domain: Base domain for DNS records (e.g., "example.com").
        dry_run: If True, generate and display the config without applying.

    Raises:
        subprocess.CalledProcessError: If terraform init or apply fails.
    """
    if not (TERRAFORM_PATH / "main.tf").exists():
        logging.warning("Terraform configuration not found. Skipping DNS management.")
        return

    public_ip = _get_public_ip()
    logging.info(f"Detected Public IP: {public_ip}")

    tf_vars = {
        "domain": domain,
        "public_ip": public_ip,
        "subdomains": services,
        "proxied": False,
    }

    tf_vars_path = TERRAFORM_PATH / "terraform.tfvars.json"

    if dry_run:
        logging.info("[DRY RUN] Would generate terraform.tfvars.json:")
        logging.info(json.dumps(tf_vars, indent=2))
        logging.info("[DRY RUN] Would run Terraform apply")
        return

    logging.info(f"Generating Terraform config for {len(services)} services...")
    with open(tf_vars_path, "w") as f:
        json.dump(tf_vars, f, indent=2)

    logging.info("Applying Cloudflare DNS updates...")
    try:
        run_command(["terraform", "init"], cwd=TERRAFORM_PATH, capture=True)
        run_command(["terraform", "apply", "-auto-approve"], cwd=TERRAFORM_PATH)
        logging.info("DNS records updated successfully!")
    except subprocess.CalledProcessError:
        logging.error("Terraform failed. Check configuration.")
        raise
