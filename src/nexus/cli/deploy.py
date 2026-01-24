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
    ALL_SERVICES,
    PRESETS,
    TERRAFORM_PATH,
    VAULT_PATH,
    resolve_preset,
)
from nexus.deploy.ansible import run_ansible
from nexus.deploy.terraform import get_gateway_dns_ips, run_terraform
from nexus.generate.dashboard import (
    generate_bookmarks_config,
    generate_dashboard_config,
    generate_settings_config,
    generate_widgets_config,
)
from nexus.utils import read_vault


def _check_dependencies() -> list[str]:
    required = ["docker", "terraform", "ansible-vault", "cloudflared"]
    missing = []

    for tool in required:
        if not shutil.which(tool):
            missing.append(tool)

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


def _is_vault_encrypted() -> bool:
    if not VAULT_PATH.exists():
        return False

    with open(VAULT_PATH) as f:
        first_line = f.readline()
    return first_line.startswith("$ANSIBLE_VAULT")


def _encrypt_vault() -> None:
    logging.info("Encrypting vault.yml...")
    subprocess.run(
        ["ansible-vault", "encrypt", str(VAULT_PATH)],
        check=True,
    )
    logging.info("✅ Vault encrypted")


def _get_tunnel_token() -> Optional[str]:
    try:
        result = subprocess.run(
            ["terraform", "output", "-raw", "tunnel_token"],
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
    logging.info("Generating dashboard configuration...")

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

    dashboard_config = generate_dashboard_config(
        services, domain or "example.com", dry_run
    )
    settings_config = generate_settings_config()
    bookmarks_config = generate_bookmarks_config()
    widgets_config = generate_widgets_config()

    if dry_run:
        logging.info(
            f"[DRY RUN] Would write dashboard config to {dashboard_config_path}"
        )
        logging.info(f"[DRY RUN] Would write settings to {settings_path}")
        logging.info(f"[DRY RUN] Would write bookmarks to {bookmarks_path}")
        logging.info(f"[DRY RUN] Would write widgets to {widgets_path}")
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
    "--skip-ansible",
    is_flag=True,
    default=False,
    help="Skip Ansible deployment (only generate configs).",
)
@click.option(
    "--skip-cloudflared",
    is_flag=True,
    default=False,
    help="Skip starting cloudflared.",
)
@click.option(
    "--use-tunnel/--no-tunnel",
    default=True,
    help="Use Cloudflare Tunnel (default) or legacy A records.",
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
    skip_ansible: bool,
    skip_cloudflared: bool,
    use_tunnel: bool,
    dry_run: bool,
    yes: bool,
) -> None:
    """Execute the complete Nexus deployment pipeline.

    Orchestrates the full deployment flow: validates prerequisites, encrypts
    secrets, provisions Cloudflare infrastructure via Terraform, starts the
    tunnel connector, and deploys services through Ansible.

    Args:
        services: Specific service names to deploy. Overrides preset.
        verbose: Enable debug-level logging output.
        all: Deploy all available services.
        preset: Named service group to deploy (e.g., "core", "home").
        domain: Base domain for service URLs (e.g., "example.com").
        skip_dns: Skip Terraform DNS/tunnel provisioning.
        skip_ansible: Skip Ansible deployment phase.
        skip_cloudflared: Skip starting the cloudflared tunnel connector.
        use_tunnel: Use Cloudflare Tunnel (True) or legacy A records (False).
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
            "terraform": "  brew install terraform / apt install terraform",
            "ansible-vault": "  brew install ansible / apt install ansible",
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

    # Check vault exists
    if not VAULT_PATH.exists():
        vault_sample = VAULT_PATH.parent / "vault.yml.sample"
        if vault_sample.exists():
            logging.error("vault.yml not found!")
            logging.info("Run: invoke setup")
            logging.info("Then edit ansible/vars/vault.yml with your secrets")
        else:
            logging.error("vault.yml.sample not found! Is this a valid nexus checkout?")
        sys.exit(1)

    # =========================================================================
    # Step 2: Confirm and gather info
    # =========================================================================

    # Determine services
    if all:
        services_list = ALL_SERVICES
    elif preset:
        services_list = resolve_preset(preset)
    elif services:
        services_list = list(services)
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
        logging.info("Set nexus_domain in vault.yml or use --domain")
        sys.exit(1)

    # Show deployment plan
    dns_mode = "Tunnel" if use_tunnel else "A Records"
    vault_status = "Encrypted" if _is_vault_encrypted() else "⚠️  NOT ENCRYPTED"
    network_status = "Exists" if _check_docker_network() else "Will create"

    print(f"\nServices: {', '.join(services_list)}")
    print(f"Domain: {domain}")
    print(f"DNS Mode: {dns_mode}")
    print(f"Vault: {vault_status}")
    print(f"Docker Network: {network_status}")
    print(f"Dry Run: {'Yes' if dry_run else 'No'}")
    print("=" * 60)

    if not yes and not dry_run:
        print("\n⚠️  Prerequisites check:")
        print("   1. Have you configured ansible/vars/vault.yml?")
        print("   2. Have you configured tailscale/access-rules.yml with user emails?")
        print("   3. Have you uploaded tailscale/acl-policy.jsonc to Tailscale Admin?")
        print("   4. Is Docker running?")
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
    # Step 4: Encrypt vault if needed
    # =========================================================================
    if not _is_vault_encrypted():
        if dry_run:
            logging.info("[DRY RUN] Would encrypt vault.yml")
        else:
            logging.info("\n📦 Vault is not encrypted. Encrypting now...")
            logging.info("   You'll be prompted to create a vault password.")
            logging.info("   ⚠️  SAVE THIS PASSWORD - needed for future deploys!\n")
            _encrypt_vault()

    # =========================================================================
    # Step 5: Run Terraform for DNS/Tunnel
    # =========================================================================
    if not skip_dns:
        logging.info("\n🌐 Setting up Cloudflare Tunnel...")
        try:
            run_terraform(services_list, domain, dry_run, use_tunnel)
        except ValueError as e:
            logging.error(f"Terraform error: {e}")
            logging.info("Fix vault.yml configuration and retry, or use --skip-dns")
            sys.exit(1)

    # =========================================================================
    # Step 6: Start cloudflared
    # =========================================================================
    if use_tunnel and not skip_cloudflared and not skip_dns:
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
    # Step 8: Deploy with Ansible
    # =========================================================================
    if not skip_ansible:
        logging.info("\n🚀 Deploying services...")
        run_ansible(services_list, dry_run)

    # =========================================================================
    # Done!
    # =========================================================================
    if dry_run:
        logging.info("\n[Dry Run Complete] No changes were made.")
    else:
        # Get Gateway DNS IPs for the summary
        gateway_primary, gateway_backup = get_gateway_dns_ips()

        print("\n" + "=" * 60)
        print("  ✅ Deployment Complete!")
        print("=" * 60)
        print("\nAccess your services (via Tailscale):")
        print(f"  Dashboard: https://hub.{domain}")
        print(f"  FoundryVTT: https://foundry.{domain} (also public via Cloudflare)")
        print("\n⚠️  Manual step required:")
        print("   Tag server: tailscale up --advertise-tags=tag:nexus-server")
        if gateway_primary:
            print("\n📡 Cloudflare Gateway DNS:")
            print("   Add to Tailscale Admin → DNS → Nameservers:")
            print(f"     Primary: {gateway_primary}")
            if gateway_backup:
                print(f"     Backup:  {gateway_backup}")
            print("   Enable 'Override Local DNS'")
            print("   (Handles split DNS + ad-blocking)")
        print("\nUseful commands:")
        print("  invoke logs --service traefik  # View logs")
        print("  invoke ps                      # Show containers")
        print(f"  invoke health --domain {domain}  # Health check")
        print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
