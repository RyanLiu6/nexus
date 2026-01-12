#!/usr/bin/env python3
import logging
from typing import Optional

import click

from nexus.config import (
    ALL_SERVICES,
    PRESETS,
    SERVICES_PATH,
    get_base_domain,
    resolve_preset,
)
from nexus.generate.dashboard import generate_dashboard_config


@click.command()
@click.argument("services", nargs=-1, required=False)
@click.option("-v", "--verbose", is_flag=True, default=False, help="Verbose mode.")
@click.option(
    "-a", "--all", is_flag=True, default=False, help="Generate config for all services."
)
@click.option(
    "-p",
    "--preset",
    type=click.Choice(list(PRESETS.keys())),
    default=None,
    help="Use a service preset.",
)
@click.option(
    "-d", "--domain", type=str, default=None, help="Base domain (e.g., ryanliu6.xyz)."
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
    preset: Optional[str],
    domain: Optional[str],
    dry_run: bool,
) -> None:
    """Generate dashboard configuration and environment variables.

    Args:
        services: List of services to generate config for.
        verbose: Enable verbose logging.
        all: Generate config for all services.
        preset: Use a service preset.
        domain: Base domain.
        dry_run: Preview changes without making them.
    """
    log_level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(level=log_level, format="%(levelname)s: %(message)s")

    if all:
        services_list = ALL_SERVICES
    elif preset:
        services_list = resolve_preset(preset)
    elif services:
        services_list = list(services)
    else:
        logging.error("No services specified. Use --all, --preset, or list services.")
        return

    logging.info(f"Services selected: {services_list}")

    if not domain:
        domain = get_base_domain()
        if not domain:
            logging.warning(
                "Domain not found. Use --domain or set NEXUS_DOMAIN env var."
            )

    dashboard_config_path = SERVICES_PATH / "dashboard" / "config" / "services.yaml"

    dashboard_config = generate_dashboard_config(
        services_list, domain or "example.com", dry_run
    )

    if dry_run:
        logging.info(
            f"[DRY RUN] Would write dashboard config to {dashboard_config_path}"
        )
    else:
        logging.info(f"Writing dashboard config to {dashboard_config_path}")
        dashboard_config_path.parent.mkdir(parents=True, exist_ok=True)
        import yaml

        with dashboard_config_path.open("w") as f:
            yaml.dump(dashboard_config, f, default_flow_style=False, sort_keys=False)

    logging.info("Dashboard configuration generated successfully!")


if __name__ == "__main__":
    main()
