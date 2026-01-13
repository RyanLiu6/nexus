import logging

from nexus.config import SERVICES_PATH
from nexus.utils import read_vault


def generate_authelia_config(domain: str, dry_run: bool = False) -> None:
    """Generate Authelia configuration file from sample template.

    Reads the sample configuration file and replaces placeholder domain
    with the actual domain to create a working Authelia configuration.

    Args:
        domain: The base domain to use (e.g., "example.com"). All
            occurrences of "example.com" in the sample will be replaced.
        dry_run: If True, log what would be done without writing files.
    """
    auth_dir = SERVICES_PATH / "auth"
    sample_config = auth_dir / "configuration.yml.sample"
    target_config = auth_dir / "configuration.yml"

    if not sample_config.exists():
        logging.warning(f"Authelia sample config not found at {sample_config}")
        return

    logging.info(f"Generating Authelia config for domain: {domain}")

    content = sample_config.read_text()
    new_content = content.replace("example.com", domain)

    if dry_run:
        logging.info(f"[DRY RUN] Would write Authelia config to {target_config}")
    else:
        target_config.write_text(new_content)
        logging.info("Authelia config generated.")


def generate_traefik_config(dry_run: bool = False) -> None:
    """Generate Traefik configuration file from sample template.

    Reads the sample configuration file and replaces environment variable
    placeholders with actual values from vault.

    Args:
        dry_run: If True, log what would be done without writing files.
    """
    traefik_dir = SERVICES_PATH / "traefik"
    sample_config = traefik_dir / "traefik.yml.sample"
    target_config = traefik_dir / "traefik.yml"

    if not sample_config.exists():
        logging.warning(f"Traefik sample config not found at {sample_config}")
        return

    logging.info("Generating Traefik config with secrets from vault")

    try:
        vault = read_vault()
        acme_email = vault.get("acme_email", "")
    except Exception as e:
        logging.error(f"Failed to read vault: {e}")
        return

    content = sample_config.read_text()
    new_content = content.replace("${ACME_EMAIL}", acme_email)

    if dry_run:
        logging.info(f"[DRY RUN] Would write Traefik config to {target_config}")
    else:
        target_config.write_text(new_content)
        logging.info("Traefik config generated.")


def generate_traefik_middlewares(domain: str, dry_run: bool = False) -> None:
    """Generate Traefik middlewares configuration from sample template.

    Reads the sample middlewares file and replaces domain placeholder
    with actual domain for the Authelia forwardAuth redirect.

    Args:
        domain: The base domain to use (e.g., "example.com").
        dry_run: If True, log what would be done without writing files.
    """
    rules_dir = SERVICES_PATH / "traefik" / "rules"
    sample_config = rules_dir / "middlewares.yml.sample"
    target_config = rules_dir / "middlewares.yml"

    if not sample_config.exists():
        logging.warning(f"Middlewares sample config not found at {sample_config}")
        return

    logging.info(f"Generating Traefik middlewares for domain: {domain}")

    content = sample_config.read_text()
    new_content = content.replace("${NEXUS_DOMAIN}", domain)

    if dry_run:
        logging.info(f"[DRY RUN] Would write middlewares config to {target_config}")
    else:
        target_config.write_text(new_content)
        logging.info("Traefik middlewares config generated.")
