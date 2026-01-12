import os

from invoke import task

# =============================================================================
# Core Development Tasks
# =============================================================================


@task
def test(c, verbose=False, coverage=True):
    """
    Run pytest with coverage.
    """
    verbose_flag = "-v" if verbose else ""
    cov_flag = "--cov=src/nexus --cov-report=term-missing" if coverage else ""
    c.run(f"uv run pytest {verbose_flag} {cov_flag}")


@task
def test_ci(c):
    """
    Run tests for CI with XML output.
    """
    c.run(
        "uv run pytest --cov=src/nexus --cov-report=xml --cov-report=term-missing "
        "--junitxml=test-results.xml"
    )


# =============================================================================
# Linting & Formatting
# =============================================================================


@task
def ruff_check(c, fix=False):
    """
    Check code with ruff.
    """
    print("Checking code with ruff...")
    fix_arg = "--fix --show-fixes" if fix else ""
    c.run(f"uv run ruff check src/ {fix_arg}")


@task
def ruff_format(c, check_only=False):
    """
    Format code with ruff.
    """
    print("Formatting code with ruff...")
    check_arg = "--check" if check_only else ""
    c.run(f"uv run ruff format src/ {check_arg}")


@task
def mypy(c):
    """
    Run mypy type checking.
    """
    print("Type checking with mypy...")
    c.run("uv run mypy src/")


@task
def lint(c):
    """
    Run all linting checks (ruff check, ruff format --check, mypy).
    """
    ruff_check(c)
    ruff_format(c, check_only=True)
    mypy(c)


@task
def format(c):
    """
    Format and fix all code issues.
    """
    ruff_check(c, fix=True)
    ruff_format(c)


# =============================================================================
# Deployment Tasks
# =============================================================================


@task
def deploy(
    c,
    services=None,
    preset=None,
    all_services=False,
    skip_dns=False,
    skip_ansible=False,
    skip_cloudflared=False,
    no_tunnel=False,
    dry_run=False,
    yes=False,
):
    """
    Deploy Nexus services (handles everything: vault, terraform, cloudflared, ansible).

    --services         Comma-separated list of services to deploy
    --preset           Service preset to deploy (core, home)
    --all              Deploy all services
    --skip-dns         Skip Terraform DNS/tunnel management
    --skip-ansible     Skip Ansible deployment
    --skip-cloudflared Skip starting cloudflared
    --no-tunnel        Use legacy A records instead of Cloudflare Tunnel
    --dry-run          Preview changes without applying
    --yes              Skip confirmation prompts

    Examples:
        invoke deploy                           # Deploy 'home' preset (default)
        invoke deploy --preset core             # Deploy core services only
        invoke deploy --services traefik,auth   # Deploy specific services
        invoke deploy --all                     # Deploy all available services
    """
    args = []

    if services:
        # Split comma-separated services and pass as positional args
        for svc in services.split(","):
            args.append(svc.strip())
    elif all_services:
        args.append("--all")
    elif preset:
        args.append(f"-p {preset}")
    else:
        # Default to home preset
        args.append("-p home")

    if skip_dns:
        args.append("--skip-dns")
    if skip_ansible:
        args.append("--skip-ansible")
    if skip_cloudflared:
        args.append("--skip-cloudflared")
    if no_tunnel:
        args.append("--no-tunnel")
    if dry_run:
        args.append("--dry-run")
    if yes:
        args.append("-y")

    c.run(f"uv run python -m nexus.cli.deploy {' '.join(args)}")


@task
def generate_dashboard(c, preset="home", domain=None):
    """
    Generate dashboard configuration.

    --preset  Service preset to generate for
    --domain  Base domain
    """
    args = [f"-p {preset}"]
    if domain:
        args.append(f"-d {domain}")
    c.run(f"uv run python -m nexus.cli.deploy --skip-dns --skip-ansible {' '.join(args)}")


# =============================================================================
# Docker Tasks
# =============================================================================


@task
def up(c, service=None):
    """
    Start Docker services.
    """
    service_arg = service if service else ""
    c.run(f"docker compose up -d {service_arg}")


@task
def down(c):
    """
    Stop all Docker services.
    """
    c.run("docker compose down")


@task
def logs(c, service=None, follow=False):
    """
    View Docker logs.
    """
    service_arg = service if service else ""
    follow_arg = "-f" if follow else ""
    c.run(f"docker compose logs {follow_arg} {service_arg}")


@task
def ps(c):
    """
    Show running containers.
    """
    c.run("docker compose ps")


@task
def pull(c):
    """
    Pull latest images for all services.
    """
    c.run("docker compose pull")


@task
def restart(c, service=None):
    """
    Restart services.
    """
    service_arg = service if service else ""
    c.run(f"docker compose restart {service_arg}")


# =============================================================================
# Health & Operations
# =============================================================================


@task
def health(c, domain=None, verbose=False):
    """
    Run health checks.

    --domain   Base domain for SSL checks
    --verbose  Enable verbose output
    """
    args = []
    if domain:
        args.append(f"--domain {domain}")
    if verbose:
        args.append("-v")
    c.run(f"uv run python -m nexus.cli.health {' '.join(args)}")


@task
def ops(c, daily=False, weekly=False, monthly=False, all_tasks=False):
    """
    Run operations/maintenance tasks.

    --daily    Run daily tasks
    --weekly   Run weekly tasks
    --monthly  Run monthly tasks
    --all      Run all tasks
    """
    args = []
    if daily:
        args.append("--daily")
    if weekly:
        args.append("--weekly")
    if monthly:
        args.append("--monthly")
    if all_tasks:
        args.append("--all")
    c.run(f"uv run python -m nexus.cli.operations {' '.join(args)}")


# =============================================================================
# Backup & Restore
# =============================================================================


@task
def backup_list(c):
    """
    List available backups.
    """
    c.run("uv run python -m nexus.cli.restore --list")


@task
def backup_verify(c, backup=None):
    """
    Verify backup integrity.
    """
    args = ["--verify"]
    if backup:
        args.append(f"--backup {backup}")
    c.run(f"uv run python -m nexus.cli.restore {' '.join(args)}")


@task
def restore(c, backup, service=None, dry_run=False):
    """
    Restore from backup.

    --backup   Backup file to restore from
    --service  Specific service to restore
    --dry-run  Preview restore without executing
    """
    args = [f"--backup {backup}"]
    if service:
        args.append(f"--service {service}")
    if dry_run:
        args.append("--dry-run")
    c.run(f"uv run python -m nexus.cli.restore {' '.join(args)}")


# =============================================================================
# Ansible Tasks
# =============================================================================


@task
def ansible_check(c):
    """
    Check Ansible playbook syntax.
    """
    c.run("ansible-playbook ansible/playbook.yml --syntax-check")


@task
def ansible_run(c, services="all", check=False):
    """
    Run Ansible playbook.

    --services  Comma-separated list of services or 'all'
    --check     Run in check mode (dry-run)
    """
    check_arg = "--check" if check else ""
    c.run(
        f"ansible-playbook ansible/playbook.yml "
        f"--extra-vars 'services={services}' "
        f"--ask-vault-pass {check_arg}"
    )


# =============================================================================
# Terraform Tasks
# =============================================================================


@task
def tf_init(c):
    """
    Initialize Terraform.
    """
    c.run("terraform -chdir=terraform init")


@task
def tf_plan(c):
    """
    Show Terraform plan (reads credentials and domain from vault.yml).
    """
    c.run(
        'uv run python -c "'
        "from nexus.deploy.terraform import apply_tunnel; "
        "apply_tunnel(dry_run=True)"
        '"'
    )


@task
def tf_apply(c):
    """
    Apply Terraform changes (reads credentials and domain from vault.yml).
    """
    c.run(
        'uv run python -c "'
        "from nexus.deploy.terraform import apply_tunnel; "
        "apply_tunnel(dry_run=False)"
        '"'
    )


# =============================================================================
# Alert Bot
# =============================================================================


@task
def alert_bot(c, port=8080):
    """
    Run the Discord alert bot.

    --port  Port to run the webhook server on
    """
    c.run(f"uv run python -m nexus.cli.alert_bot --port {port}")


# =============================================================================
# Setup Tasks
# =============================================================================


@task
def setup_network(c):
    """
    Create Docker proxy network.
    """
    result = c.run("docker network ls --format '{{.Name}}'", hide=True)
    if "proxy" not in result.stdout:
        c.run("docker network create proxy")
        print("✅ Created 'proxy' network")
    else:
        print("✅ 'proxy' network already exists")


@task
def setup_vault(c):
    """
    Create vault.yml from sample if it doesn't exist.
    """
    import shutil
    from pathlib import Path

    vault_path = Path("ansible/vars/vault.yml")
    sample_path = Path("ansible/vars/vault.yml.sample")

    if vault_path.exists():
        print("⚠️  vault.yml already exists. Edit it manually.")
    elif sample_path.exists():
        shutil.copy(sample_path, vault_path)
        print("✅ Created vault.yml from sample. Edit it with your secrets.")
        print("   Then encrypt: ansible-vault encrypt ansible/vars/vault.yml")
    else:
        print("❌ vault.yml.sample not found!")


@task
def setup(c):
    """
    Run all setup tasks.
    """
    setup_network(c)
    setup_vault(c)
    print("\n✅ Setup complete! Next steps:")
    print("   1. Edit ansible/vars/vault.yml with your secrets")
    print("   2. Encrypt vault: ansible-vault encrypt ansible/vars/vault.yml")
    print("   3. Deploy: invoke deploy")
