import logging
import subprocess

from nexus.config import ANSIBLE_PATH
from nexus.utils import run_command


def run_ansible(services: list[str], dry_run: bool = False) -> None:
    """Execute the Ansible playbook to deploy Docker services.

    Runs the main playbook with the specified services passed as extra
    variables. The playbook handles container orchestration and configuration.

    Args:
        services: List of service names to deploy (e.g., ["traefik", "auth"]).
            These are passed to ansible-playbook as a comma-separated string.
        dry_run: If True, log the intended actions without executing the playbook.

    Raises:
        FileNotFoundError: If the Ansible playbook does not exist.
        subprocess.CalledProcessError: If ansible-playbook returns non-zero exit code.
    """
    if not (ANSIBLE_PATH / "playbook.yml").exists():
        logging.error("Ansible playbook not found. Cannot deploy services.")
        raise FileNotFoundError("Ansible playbook not found")

    if dry_run:
        logging.info("[DRY RUN] Would run Ansible playbook for services:")
        services_str = ",".join(services)
        logging.info(f"[DRY RUN] Services: {services_str}")
        logging.info(f"[DRY RUN] Playbook: {ANSIBLE_PATH / 'playbook.yml'}")
        return

    logging.info("Deploying services with Ansible...")

    services_str = ",".join(services)

    try:
        run_command(
            [
                "ansible-playbook",
                "playbook.yml",
                "--extra-vars",
                f"services={services_str}",
            ],
            cwd=ANSIBLE_PATH,
        )
        logging.info("Services deployed successfully!")
    except subprocess.CalledProcessError:
        logging.error("Ansible deployment failed. Please check logs.")
        raise
