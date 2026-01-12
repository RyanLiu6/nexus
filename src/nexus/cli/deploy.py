import logging
import os
import shutil
import sys

import click
import yaml

from nexus.config import ALL_SERVICES, PRESETS, SERVICES_PATH, resolve_preset
from nexus.deploy.ansible import run_ansible
from nexus.deploy.auth import generate_authelia_config
from nexus.deploy.terraform import run_terraform
from nexus.generate.dashboard import generate_dashboard_config


def _check_dependencies() -> None:
    required = ["docker", "terraform", "ansible"]
    missing = []

    for tool in required:
        if not shutil.which(tool):
            missing.append(tool)

    if missing:
        logging.error(f"Missing required tools: {', '.join(missing)}")
        logging.info("Install missing tools:")
        for tool in missing:
            if tool == "terraform":
                logging.info(
                    "  Terraform: https://developer.hashicorp.com/terraform/downloads"
                )
            elif tool == "ansible":
                logging.info(
                    "  Ansible: sudo apt install ansible (Ubuntu) "
                    "or brew install ansible (macOS)"
                )
            elif tool == "docker":
                logging.info("  Docker: https://docs.docker.com/get-docker/")
        sys.exit(1)


def _generate_configs(
    services: list[str], domain: str | None, dry_run: bool = False
) -> None:
    logging.info("Generating configuration files...")

    dashboard_config_path = SERVICES_PATH / "dashboard" / "config" / "services.yaml"
    dashboard_config = generate_dashboard_config(
        services, domain or "example.com", dry_run
    )

    if dry_run:
        logging.info(
            f"[DRY RUN] Would write dashboard config to {dashboard_config_path}"
        )
    else:
        logging.info(f"Writing dashboard config to {dashboard_config_path}")
        dashboard_config_path.parent.mkdir(parents=True, exist_ok=True)
        with dashboard_config_path.open("w") as f:
            yaml.dump(dashboard_config, f, default_flow_style=False, sort_keys=False)

    if domain:
        generate_authelia_config(domain, dry_run)


@click.command()
@click.argument("services", nargs=-1, required=False)
@click.option("-v", "--verbose", is_flag=True, default=False, help="Verbose mode.")
@click.option("-a", "--all", is_flag=True, default=False, help="Deploy all services.")
@click.option(
    "-p",
    "--preset",
    type=click.Choice(list(PRESETS.keys())),
    default=None,
    help="Use a service preset.",
)
@click.option(
    "-d", "--domain", type=str, default=None, help="Base domain (e.g., example.com)."
)
@click.option("--skip-dns", is_flag=True, default=False, help="Skip DNS management.")
@click.option(
    "--skip-ansible",
    is_flag=True,
    default=False,
    help="Skip Ansible deployment (only generate configs).",
)
@click.option(
    "--dry-run",
    is_flag=True,
    default=False,
    help="Preview changes without making them.",
)
def main(
    services: tuple[str, ...],
    verbose: bool,
    all: bool,
    preset: str | None,
    domain: str | None,
    skip_dns: bool,
    skip_ansible: bool,
    dry_run: bool,
) -> None:
    """Deploy Nexus services with Terraform (DNS) and Ansible (containers)."""
    log_level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(level=log_level, format="%(levelname)s: %(message)s")

    _check_dependencies()

    if all:
        services_list = ALL_SERVICES
    elif preset:
        services_list = resolve_preset(preset)
    elif services:
        services_list = list(services)
    else:
        logging.error("No services specified. Use --all, --preset, or list services.")
        return

    logging.info(f"Services to deploy: {services_list}")

    if not domain:
        domain = os.environ.get("NEXUS_DOMAIN")
        if not domain:
            logging.warning(
                "Domain not specified. Use --domain or set NEXUS_DOMAIN env var."
            )

    print("\n" + "=" * 60)
    print("  Nexus Deployment")
    print("=" * 60)
    print(f"Services: {', '.join(services_list)}")
    print(f"Domain: {domain or 'Not set'}")
    print(f"DNS Management: {'Enabled' if not skip_dns else 'Disabled'}")
    print(f"Ansible Deployment: {'Enabled' if not skip_ansible else 'Disabled'}")
    print(f"Dry Run: {'Yes' if dry_run else 'No'}")
    print("=" * 60 + "\n")

    if not skip_dns:
        if not domain:
            logging.warning("Domain not set, skipping DNS management")
        else:
            run_terraform(services_list, domain, dry_run)

    _generate_configs(services_list, domain, dry_run)

    if not skip_ansible:
        run_ansible(services_list, dry_run)

    if dry_run:
        logging.info("\n[Dry Run Complete] No changes were made.")
    else:
        logging.info("\nDeployment complete! 🚀")
        if domain:
            logging.info(f"Access your dashboard at: https://hub.{domain}")


if __name__ == "__main__":
    main()
