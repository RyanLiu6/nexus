#!/usr/bin/env python

import os
import click
import pathlib


@click.group()
def cli():
    pass


@cli.command()
@click.argument("username")
def generate_official(username: str) -> None:
    """
    Generates Systemd config file for ProtonVPN-CLI (Official Edition).

    Args:
        username (str): Username that you registered ProtonVPN-CLi with
    """
    folder_path = pathlib.Path(__file__).parent.resolve()
    template_path = os.path.join(folder_path, "template_official.service")
    service_path = "/etc/systemd/system/protonvpn-autoconnect.service"

    generate_helper(template_path=template_path, config_output_path=service_path, username=username)


@cli.command()
@click.argument("username")
def generate_community(username: str) -> None:
    """
    Generates Systemd config file for ProtonVPN-CLI (Community Edition).

    Args:
        username (str): Username that you registered ProtonVPN-CLi with
    """
    folder_path = pathlib.Path(__file__).parent.resolve()
    template_path = os.path.join(folder_path, "template_community.service")
    service_path = "/etc/systemd/system/protonvpn-autoconnect.service"

    generate_helper(template_path=template_path, config_output_path=service_path, username=username)


def generate_helper(template_path, config_output_path, username):
    with open(template_path, "r") as template_file:
        template = template_file.read()

    template = template.format(user=username)

    with open(config_output_path, "w+") as write_file:
        write_file.write(template)


if __name__ == "__main__":
    cli()
