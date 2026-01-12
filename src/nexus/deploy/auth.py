import logging

from nexus.config import SERVICES_PATH


def generate_authelia_config(domain: str, dry_run: bool = False) -> None:
    """Generate Authelia configuration from sample, injecting domain.

    Args:
        domain: The base domain (e.g., ryanliu6.xyz)
        dry_run: If True, do not write changes.
    """
    auth_dir = SERVICES_PATH / "auth"
    sample_config = auth_dir / "configuration.yml.sample"
    target_config = auth_dir / "configuration.yml"

    if not sample_config.exists():
        logging.warning(f"Authelia sample config not found at {sample_config}")
        return

    logging.info(f"Generating Authelia config for domain: {domain}")

    # Read sample
    content = sample_config.read_text()

    # Replace placeholders
    # We replace 'example.com' with the actual domain
    new_content = content.replace("example.com", domain)

    if dry_run:
        logging.info(f"[DRY RUN] Would write Authelia config to {target_config}")
    else:
        target_config.write_text(new_content)
        logging.info("Authelia config generated.")
