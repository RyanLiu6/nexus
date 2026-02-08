import logging
import os
import subprocess
from typing import Optional

from nexus.config import ANSIBLE_PATH
from nexus.types import R2Credentials
from nexus.utils import run_command


def run_ansible(
    services: list[str],
    dry_run: bool = False,
    r2_credentials: Optional[R2Credentials] = None,
) -> None:
    """Execute the Ansible playbook to deploy Docker services.

    Runs the main playbook with the specified services passed as extra
    variables. The playbook handles container orchestration and configuration.

    Args:
        services: List of service names to deploy (e.g., ["traefik", "auth"]).
            These are passed to ansible-playbook as a comma-separated string.
        dry_run: If True, log the intended actions without executing the playbook.
        r2_credentials: Optional R2 credentials from Terraform. If provided,
            these are passed as extra-vars to override vault values for
            Foundry S3 configuration.

    Raises:
        FileNotFoundError: If the Ansible playbook does not exist.
        subprocess.CalledProcessError: If ansible-playbook returns non-zero exit code.
    """
    if not (ANSIBLE_PATH / "playbook.yml").exists():
        logging.error("Ansible playbook not found. Cannot deploy services.")
        raise FileNotFoundError("Ansible playbook not found")

    services_str = ",".join(services)
    extra_vars = [f"services={services_str}"]

    # Pass environment overrides if set
    if data_dir := os.environ.get("NEXUS_DATA_DIRECTORY"):
        extra_vars.append(f"nexus_data_directory={data_dir}")

    if email := os.environ.get("ACME_EMAIL"):
        extra_vars.append(f"acme_email={email}")

    # Pass R2 credentials from Terraform if provided
    if r2_credentials:
        extra_vars.append(f"foundry_s3_endpoint={r2_credentials['endpoint']}")
        extra_vars.append(f"foundry_s3_access_key={r2_credentials['access_key']}")
        extra_vars.append(f"foundry_s3_secret_key={r2_credentials['secret_key']}")
        extra_vars.append(f"foundry_s3_bucket={r2_credentials['bucket']}")

    extra_vars_str = " ".join(extra_vars)

    if dry_run:
        logging.info("[DRY RUN] Would run Ansible playbook for services:")
        logging.info(f"[DRY RUN] Services: {services_str}")
        logging.info(f"[DRY RUN] Extra Vars: {extra_vars_str}")
        logging.info(f"[DRY RUN] Playbook: {ANSIBLE_PATH / 'playbook.yml'}")
        return

    logging.info("Deploying services with Ansible...")

    try:
        run_command(
            [
                "ansible-playbook",
                "ansible/playbook.yml",
                "--extra-vars",
                extra_vars_str,
            ],
        )
        logging.info("Services deployed successfully!")
    except subprocess.CalledProcessError:
        logging.error("Ansible deployment failed. Please check logs.")
        raise
