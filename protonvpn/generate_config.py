#!/usr/bin/env python

import os
import pathlib

import click


@click.command()
@click.argument("username")
def generate_config(username: str) -> None:
    """
    Generates Systemd config file for ProtonVPN-CLI.

    Args:
        username (str): Username that you registered ProtonVPN-CLi with
    """
    folder_path = pathlib.Path(__file__).parent.resolve()
    template_path = os.path.join(folder_path, "template.service")

    with open(template_path, "rw") as template_file:
        template = template_file.read()

    template.format(user=username)

    service_path = "/etc/systemd/system/protonvpn-autoconnect.service"
    with open(service_path, "w+") as write_file:
        write_file.write(template)


if __name__ == "__main__":
    generate_config()
