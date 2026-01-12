import logging

from nexus.config import SERVICES_PATH


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
