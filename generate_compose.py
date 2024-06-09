#!/usr/bin/env python3

import os
import click
import logging

from typing import List

from vigor.compose import Compose
from vigor.utils import get_immediate_subdirectories

# Some global stuff I don't know how to not abstract
ROOT_PATH = os.path.dirname(os.path.abspath(__name__))
ALL_SERVICES = get_immediate_subdirectories(full_path=ROOT_PATH, ignore=[".git"])
CORE_SERVICES = ["traefik"]


@click.command()
@click.argument("services", type=click.Choice(ALL_SERVICES), nargs=-1)
@click.option("-v", "--verbose", is_flag=True, default=False, help="Verbose mode.")
@click.option("-a", "--all", is_flag=True, default=False, help="Generate Compose file for all possible services.")
def generate_config(services, verbose, all):
    """
    Generates aggregated docker-compose.yml for services.
    """
    log_level = logging.INFO if verbose else logging.WARNING
    logging.basicConfig(level=log_level)

    if all:
        services = ALL_SERVICES
    else:
        # Is this more performant than iterating through core_services and doing `in` check with append?
        services = list(set(services + CORE_SERVICES))

    logging.info(f"Services selected: {services}")
    files = []
    for service in services:
        files.append(os.path.join(ROOT_PATH, service, "docker-compose.yml"))

    aggregated_env = aggregate_env_file(services=services)

    aggregated_compose = os.path.join(ROOT_PATH, "docker-compose.yml")
    with open(aggregated_compose, "w") as compose_file:
        compose = Compose("Focus")
        compose_config = compose.generate_compose_file(files=files, env=aggregated_env)
        compose_file.write(compose_config)
        logging.info(f"Aggregated docker-compose.yml file created at {aggregated_compose}")


def aggregate_env_file(services: List) -> str:
    """
    Aggregates all found .env files into one for aggregated docker-compose.yml file.

    Args:
        services (List): List of services to check for.

    Returns:
        str: Path to the new .env file
    """
    env_files = []
    for service in services:
        absolute_path = os.path.join(ROOT_PATH, service)
        for item in os.scandir(absolute_path):
            if item.is_file and item.name.endswith(".env"):
                env_files.append(item.path)

    # Only proceed if there's any files
    if not env_files:
        logging.info("No .env files found for selected services")
        return

    aggregate_config = {}
    for file in env_files:
        with open(file, "r") as read_file:
            for line in read_file:
                split = line.split("=")
                aggregate_config[split[0]] = split[1]

    aggregate_filename = os.path.join(ROOT_PATH, ".env")
    with open(aggregate_filename, "w") as write_file:
        for key, value in aggregate_config.items():
            write_file.write(f"{key}={value}")

    logging.info(f"Aggregated .env file created at {aggregate_filename}")

    return aggregate_filename


if __name__ == "__main__":
    generate_config()
