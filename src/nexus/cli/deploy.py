import logging
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Optional

import click
import yaml

from nexus.config import (
    PRESETS,
    TERRAFORM_PATH,
    VAULT_PATH,
    get_all_services,
    resolve_preset,
)
from nexus.deploy.terraform import (
    get_r2_credentials,
    get_tofu_cmd,
    run_terraform,
)
from nexus.generate.access_rules import sync_access_rules
from nexus.generate.dashboard import (
    generate_bookmarks_config,
    generate_custom_css,
    generate_dashboard_config,
    generate_settings_config,
    generate_widgets_config,
)
from nexus.services import discover_services, resolve_dependencies
from nexus.types import R2Credentials
from nexus.utils import read_vault


def _check_dependencies() -> list[str]:
    required = ["docker", "sops", "cloudflared"]
    missing = []

    for tool in required:
        if not shutil.which(tool):
            missing.append(tool)

    if not shutil.which("tofu") and not shutil.which("terraform"):
        missing.append("tofu")

    return missing


def _check_docker_network() -> bool:
    try:
        result = subprocess.run(
            ["docker", "network", "ls", "--format", "{{.Name}}"],
            capture_output=True,
            text=True,
            check=True,
        )
        return "nexus" in result.stdout.split("\n")
    except subprocess.CalledProcessError:
        return False


def _create_docker_network() -> None:
    logging.info("Creating Docker nexus network...")
    subprocess.run(["docker", "network", "create", "nexus"], check=True)
    logging.info("✅ Created 'nexus' network")


def _get_tunnel_token() -> Optional[str]:
    cmd = get_tofu_cmd()
    try:
        result = subprocess.run(
            [cmd, "output", "-raw", "tunnel_token"],
            cwd=TERRAFORM_PATH,
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout.strip() if result.stdout.strip() else None
    except subprocess.CalledProcessError:
        return None


def _is_cloudflared_running() -> bool:
    try:
        result = subprocess.run(
            ["pgrep", "-x", "cloudflared"],
            capture_output=True,
            check=False,
        )
        return result.returncode == 0
    except Exception:
        return False


def _start_cloudflared(token: str) -> None:
    logging.info("Starting cloudflared tunnel...")

    # Try to install as service first (recommended)
    try:
        subprocess.run(
            ["cloudflared", "service", "install", token],
            capture_output=True,
            check=True,
        )
        logging.info("✅ Cloudflared installed as service")
        return
    except subprocess.CalledProcessError:
        # Service might already exist or need sudo
        pass

    # Fall back to running in background
    logging.info("Starting cloudflared in background...")
    subprocess.Popen(
        ["cloudflared", "tunnel", "run", "--token", token],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True,
    )
    logging.info("✅ Cloudflared started in background")


def _generate_configs(
    services: list[str],
    domain: Optional[str],
    data_dir: Optional[str] = None,
    dry_run: bool = False,
) -> None:
    logging.info("Generating configurations...")

    # Generate access rules from service manifests
    if dry_run:
        logging.info("[DRY RUN] Would generate access rules from service manifests")
    else:
        rules_path = sync_access_rules(services)
        logging.info(f"Generated access rules: {rules_path}")

    # Resolve data_dir: arg -> env -> vault -> default
    if not data_dir:
        data_dir = os.environ.get("NEXUS_DATA_DIRECTORY")

    if not data_dir:
        try:
            vault = read_vault()
            data_dir = vault.get("nexus_data_directory")
        except Exception:
            pass

    if not data_dir:
        data_dir = "~/nexus-data"

    homepage_dir = Path(data_dir).expanduser() / "Config" / "homepage"
    dashboard_config_path = homepage_dir / "services.yaml"
    settings_path = homepage_dir / "settings.yaml"
    bookmarks_path = homepage_dir / "bookmarks.yaml"
    widgets_path = homepage_dir / "widgets.yaml"
    custom_css_path = homepage_dir / "custom.css"

    vault = {}
    try:
        vault = read_vault()
    except Exception:
        logging.warning("Could not read vault secrets for dashboard generation.")

    dashboard_config = generate_dashboard_config(
        services, domain or "example.com", dry_run, secrets=vault
    )
    settings_config = generate_settings_config()
    bookmarks_config = generate_bookmarks_config(domain=domain)
    widgets_config = generate_widgets_config()
    custom_css = generate_custom_css()

    if dry_run:
        logging.info(
            f"[DRY RUN] Would write dashboard config to {dashboard_config_path}"
        )
        logging.info(f"[DRY RUN] Would write settings to {settings_path}")
        logging.info(f"[DRY RUN] Would write bookmarks to {bookmarks_path}")
        logging.info(f"[DRY RUN] Would write widgets to {widgets_path}")
        logging.info(f"[DRY RUN] Would write custom css to {custom_css_path}")
    else:
        homepage_dir.mkdir(parents=True, exist_ok=True)

        logging.info(f"Writing dashboard config to {dashboard_config_path}")
        with dashboard_config_path.open("w") as f:
            yaml.dump(dashboard_config, f, default_flow_style=False, sort_keys=False)

        logging.info(f"Writing settings to {settings_path}")
        with settings_path.open("w") as f:
            yaml.dump(settings_config, f, default_flow_style=False, sort_keys=False)

        logging.info(f"Writing bookmarks to {bookmarks_path}")
        with bookmarks_path.open("w") as f:
            yaml.dump(bookmarks_config, f, default_flow_style=False, sort_keys=False)

        logging.info(f"Writing widgets to {widgets_path}")
        with widgets_path.open("w") as f:
            yaml.dump(widgets_config, f, default_flow_style=False, sort_keys=False)

        logging.info(f"Writing custom css to {custom_css_path}")
        with custom_css_path.open("w") as f:
            f.write(custom_css)


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
@click.option("--skip-dns", is_flag=True, default=False, help="Skip DNS/tunnel setup.")
@click.option(
    "--skip-deploy",
    is_flag=True,
    default=False,
    help="Skip deployment (only generate configs).",
)
@click.option(
    "--skip-cloudflared",
    is_flag=True,
    default=False,
    help="Skip starting cloudflared.",
)
@click.option(
    "--dry-run",
    is_flag=True,
    default=False,
    help="Preview changes without making them.",
)
@click.option(
    "-y",
    "--yes",
    is_flag=True,
    default=False,
    help="Skip confirmation prompts.",
)
def main(
    services: tuple[str, ...],
    verbose: bool,
    all: bool,
    preset: Optional[str],
    domain: Optional[str],
    skip_dns: bool,
    skip_deploy: bool,
    skip_cloudflared: bool,
    dry_run: bool,
    yes: bool,
) -> None:
    """Execute the complete Nexus deployment pipeline.

    Orchestrates the full deployment flow: validates prerequisites, encrypts
    secrets, provisions Cloudflare infrastructure via Terraform, starts the
    tunnel connector, and deploys services through PyInfra.

    Args:
        services: Specific service names to deploy. Overrides preset.
        verbose: Enable debug-level logging output.
        all: Deploy all available services.
        preset: Named service group to deploy (e.g., "core", "home").
        domain: Base domain for service URLs (e.g., "example.com").
        skip_dns: Skip Terraform DNS/tunnel provisioning.
        skip_deploy: Skip deployment phase.
        skip_cloudflared: Skip starting the cloudflared tunnel connector.
        dry_run: Preview changes without applying them.
        yes: Skip all confirmation prompts.

    Raises:
        SystemExit: On missing dependencies, invalid configuration, or errors.
    """
    log_level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(level=log_level, format="%(levelname)s: %(message)s")

    # =========================================================================
    # Step 1: Check prerequisites
    # =========================================================================
    print("\n" + "=" * 60)
    print("  Nexus Deployment")
    print("=" * 60)

    missing_tools = _check_dependencies()
    if missing_tools:
        logging.error(f"Missing required tools: {', '.join(missing_tools)}")
        logging.info("\nInstall missing tools:")
        install_hints = {
            "docker": "  brew install --cask docker / https://get.docker.com",
            "tofu": "  brew install opentofu / https://opentofu.org/docs/intro/install/",
            "cloudflared": "  brew install cloudflare/cloudflare/cloudflared",
        }
        for tool in missing_tools:
            if tool in install_hints:
                logging.info(install_hints[tool])
        sys.exit(1)

    # Check venv is activated
    if not os.environ.get("VIRTUAL_ENV"):
        logging.warning("Virtual environment not activated!")
        logging.info("Run: source .venv/bin/activate")
        logging.info("Or use direnv: echo 'layout uv' > .envrc && direnv allow")
        if not yes:
            if not click.confirm("Continue anyway?", default=False):
                sys.exit(1)

    # Check secrets exist
    if not VAULT_PATH.exists():
        secrets_sample = VAULT_PATH.parent / "secrets.sample.yml"
        if secrets_sample.exists():
            logging.error("secrets.enc.yml not found!")
            logging.info("Run: cp config/secrets.sample.yml config/secrets.yml")
            logging.info(
                "Then edit config/secrets.yml with your secrets, and encrypt with sops."
            )
        else:
            logging.error(
                "secrets.sample.yml not found! Is this a valid nexus checkout?"
            )
        sys.exit(1)

    # =========================================================================
    # Step 2: Confirm and gather info
    # =========================================================================

    # Determine services
    if all:
        services_list = get_all_services()
    elif preset:
        services_list = resolve_preset(preset)
    elif services:
        services_list = resolve_dependencies(list(services), discover_services())
        logging.info(f"Resolved services with dependencies: {services_list}")
    else:
        # Default to home preset
        services_list = resolve_preset("home")
        logging.info("No services specified, using 'home' preset")

    # Get domain from vault if not specified
    if not domain:
        domain = os.environ.get("NEXUS_DOMAIN")
        if not domain:
            try:
                vault = read_vault()
                domain = vault.get("nexus_domain")
                if domain == "example.com":
                    domain = None
            except Exception:
                pass

    if not domain:
        logging.error("Domain not configured!")
        logging.info("Set nexus_domain in secrets.yml or use --domain")
        sys.exit(1)

    # Show deployment plan
    vault_status = (
        "Encrypted" if "sops" in VAULT_PATH.read_text() else "⚠️  NOT ENCRYPTED"
    )
    network_status = "Exists" if _check_docker_network() else "Will create"

    print(f"\nServices: {', '.join(services_list)}")
    print(f"Domain: {domain}")
    print(f"Secrets: {vault_status}")
    print(f"Docker Network: {network_status}")
    print(f"Dry Run: {'Yes' if dry_run else 'No'}")
    print("=" * 60)

    if not yes and not dry_run:
        print("\n⚠️  Prerequisites check:")
        print("   1. Have you configured config/secrets.yml?")
        print("   2. Is Docker running?")
        if not click.confirm("\nProceed with deployment?", default=True):
            logging.info("Deployment cancelled.")
            sys.exit(0)

    # =========================================================================
    # Step 3: Create Docker network if needed
    # =========================================================================
    if not _check_docker_network():
        if dry_run:
            logging.info("[DRY RUN] Would create Docker nexus network")
        else:
            _create_docker_network()

    # =========================================================================
    # Step 4: Run Terraform for DNS/Tunnel
    # =========================================================================
    if not skip_dns:
        logging.info("\n🌐 Setting up Cloudflare Tunnel...")
        try:
            run_terraform(services_list, domain, dry_run)
        except ValueError as e:
            logging.error(f"Terraform error: {e}")
            logging.info("Fix secrets.yml configuration and retry, or use --skip-dns")
            sys.exit(1)

    # =========================================================================
    # Step 6: Start cloudflared
    # =========================================================================
    if not skip_cloudflared and not skip_dns:
        if _is_cloudflared_running():
            logging.info("✅ Cloudflared already running")
        else:
            token = _get_tunnel_token()
            if token:
                if dry_run:
                    logging.info("[DRY RUN] Would start cloudflared tunnel")
                else:
                    _start_cloudflared(token)
            else:
                logging.warning("Could not get tunnel token. Start manually:")
                logging.info("  cd terraform && terraform output -raw tunnel_token")
                logging.info("  cloudflared tunnel run --token <token>")

    # =========================================================================
    # Step 7: Generate configs
    # =========================================================================
    _generate_configs(services_list, domain, dry_run=dry_run)

    # =========================================================================
    # Step 7.5: Retrieve R2 credentials from Terraform (if applicable)
    # =========================================================================
    r2_credentials: Optional[R2Credentials] = None
    backups_r2_credentials: Optional[R2Credentials] = None
    if not skip_dns:
        if "foundryvtt" in services_list:
            r2_credentials = get_r2_credentials("foundry")
            if r2_credentials:
                logging.info("✅ Retrieved Foundry R2 credentials from Terraform")
            else:
                logging.warning("R2 credentials not available for foundryvtt")
        if "backups" in services_list:
            backups_r2_credentials = get_r2_credentials("backups")
            if backups_r2_credentials:
                logging.info("✅ Retrieved Backups R2 credentials from Terraform")
            else:
                logging.warning(
                    "R2 credentials not available for backups - local backups only"
                )

    # =========================================================================
    # Step 8: Deploy with PyInfra
    # =========================================================================
    if not skip_deploy:
        logging.info("\n🚀 Deploying services using PyInfra...")
        import subprocess

        env = os.environ.copy()
        env["NEXUS_SERVICES"] = ",".join(services_list)

        # Inject Terraform R2 outputs into environment for PyInfra
        if r2_credentials:
            env["TF_FOUNDRY_S3_ENDPOINT"] = r2_credentials["endpoint"]
            env["TF_FOUNDRY_S3_ACCESS_KEY"] = r2_credentials["access_key"]
            env["TF_FOUNDRY_S3_SECRET_KEY"] = r2_credentials["secret_key"]
        if backups_r2_credentials:
            env["TF_BACKUPS_R2_ENDPOINT"] = backups_r2_credentials["endpoint"]
            env["TF_BACKUPS_R2_ACCESS_KEY"] = backups_r2_credentials["access_key"]
            env["TF_BACKUPS_R2_SECRET_KEY"] = backups_r2_credentials["secret_key"]

        cmd = ["uv", "run", "pyinfra", "@local", "infra.py", "-y"]
        if dry_run:
            logging.info(f"[DRY RUN] Would execute: {' '.join(cmd)}")
        else:
            try:
                subprocess.run(cmd, env=env, check=True)
            except subprocess.CalledProcessError:
                logging.error("PyInfra deployment failed.")
                sys.exit(1)

    # =========================================================================
    # Done!
    # =========================================================================
    if dry_run:
        logging.info("\n[Dry Run Complete] No changes were made.")
    else:
        print("\n" + "=" * 60)
        print("  ✅ Deployment Complete!")
        print("=" * 60)
        print("\nAccess your services (via Tailscale):")
        print(f"  Dashboard: https://nexus.{domain}")
        print(f"  FoundryVTT: https://foundry.{domain} (also public via Cloudflare)")
        print(f"  Headscale: https://headscale.{domain}")

        print("\n✅ Tailscale control server (Headscale) running locally")
        print(f"   Server URL: https://headscale.{domain}")
        print("\n⚠️  Connect this server to Headscale (one-time setup):")
        print(
            f"   sudo tailscale up --login-server https://headscale.{domain} "
            "--advertise-tags=tag:nexus-server --ssh"
        )
        print("\nUseful commands:")
        print("  inv logs --service traefik  # View logs")
        print("  inv ps                      # Show containers")
        print(f"  inv health --domain {domain}  # Health check")
        print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
