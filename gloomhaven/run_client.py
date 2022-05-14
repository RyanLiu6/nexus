#!/usr/bin/env python3

import os
import click

from vigor.utils import CommandRunner


@click.command()
def run_client():
    """
    Runs a client for Gloomhaven Helper.
    """
    root_dir = os.path.dirname(os.path.abspath(__file__))
    ghh_dir = os.path.join(root_dir, "GloomhavenHelper")

    # CommandRunner would raise exception so no exception means everything is good
    if not os.path.exists(ghh_dir):
        unzip_command = ["unzip", "GloomhavenHelper-8.4.12.zip"]
        CommandRunner().run(*unzip_command)

    if os.path.isdir(ghh_dir):
        run_command = ["java", "-XstartOnFirstThread", "-jar", os.path.join(ghh_dir, "ghh.jar")]
        CommandRunner().run(*run_command)


if __name__ == "__main__":
    run_client()
