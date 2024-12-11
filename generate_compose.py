#!/usr/bin/env python3
import logging
import os
from pathlib import Path
from typing import Dict, List, Optional

import click
from vigor.compose import Compose  # type: ignore
from vigor.utils import get_immediate_subdirectories # type: ignore

# Some global stuff I don't know how to not abstract
ROOT_PATH = os.path.dirname(os.path.abspath(__file__))
ALL_SERVICES = get_immediate_subdirectories(full_path=ROOT_PATH, ignore=[".git"])
CORE_SERVICES = ["traefik"]


def parse_env_file(file_path: Path) -> Dict[str, str]:
    """Parse a single .env file and return its key-value pairs.

    Args:
        file_path (Path): Path to the .env file

    Returns:
        Dict[str, str]: Dictionary of environment variables
    """
    config: Dict[str, str] = {}
    try:
        content = file_path.read_text().strip()
        for line in content.splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" not in line:
                logging.warning(f"Skipping invalid line in {file_path}: {line}")
                continue
            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip()
            if key:
                config[key] = value
    except Exception as e:
        logging.error(f"Error reading {file_path}: {e}")
    return config


def aggregate_env_file(services: List[str]) -> Optional[Path]:
    """Aggregate all found .env files into one for aggregated docker-compose.yml file.

    Args:
        services (List[str]): List of services to check for.

    Returns:
        Optional[Path]: Path to the new .env file, or None if no files were processed
    """
    root_path = Path(ROOT_PATH)
    env_files: List[Path] = []

    # Collect all .env files
    for service in services:
        service_path = root_path / service
        if not service_path.is_dir():
            logging.warning(f"Service directory not found: {service_path}")
            continue

        env_files.extend(path for path in service_path.glob("*.env") if path.is_file())

    if not env_files:
        logging.info("No .env files found for selected services")
        return None

    # Aggregate configurations
    aggregate_config: Dict[str, str] = {}
    for file_path in env_files:
        logging.info(f"Processing .env file: {file_path}")
        new_config = parse_env_file(file_path)

        # Check for overwrites
        for key in new_config:
            if key in aggregate_config and aggregate_config[key] != new_config[key]:
                logging.warning(
                    f"Environment variable '{key}' from {file_path} "
                    f"overwrites existing value"
                )

        aggregate_config.update(new_config)

    if not aggregate_config:
        logging.warning("No valid environment variables found in any .env file")
        return None

    # Write aggregated config
    output_path = root_path / ".env"
    try:
        with output_path.open("w") as f:
            for key, value in sorted(aggregate_config.items()):
                f.write(f"{key}={value}\n")
        logging.info(f"Aggregated .env file created at {output_path}")
        return output_path
    except Exception as e:
        logging.error(f"Failed to write aggregated .env file: {e}")
        return None


@click.command()
@click.argument("services", type=click.Choice(ALL_SERVICES), nargs=-1)
@click.option("-v", "--verbose", is_flag=True, default=False, help="Verbose mode.")
@click.option(
    "-a",
    "--all",
    is_flag=True,
    default=False,
    help="Generate Compose file for all possible services.",
)
def generate_config(services: List[str], verbose: bool, all: bool) -> None:
    """
    Generates aggregated docker-compose.yml for services.
    """
    log_level = logging.INFO if verbose else logging.WARNING
    logging.basicConfig(level=log_level)

    if all:
        services = ALL_SERVICES
    else:
        # Is this more performant than iterating through core_services and doing `in` check with append?
        services = list(set(list(services) + CORE_SERVICES))

    logging.info(f"Services selected: {services}")
    files = []
    for service in services:
        files.append(os.path.join(ROOT_PATH, service, "docker-compose.yml"))

    aggregated_env = aggregate_env_file(services=services)

    aggregated_compose = os.path.join(ROOT_PATH, "docker-compose.yml")
    with open(aggregated_compose, "w") as compose_file:
        compose = Compose("focus")
        compose_config = compose.generate_compose_file(files=files, env=aggregated_env)
        compose_file.write(compose_config)
        logging.info(
            f"Aggregated docker-compose.yml file created at {aggregated_compose}"
        )


if __name__ == "__main__":
    generate_config()
