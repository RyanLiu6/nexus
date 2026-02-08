from typing import Optional

from invoke import Context, task

# =============================================================================
# Core Development Tasks
# =============================================================================


@task
def test(c: Context, verbose: bool = False, coverage: bool = True) -> None:
    """Run pytest with coverage.

    Args:
        c: Invoke context.
        verbose: Enable verbose output.
        coverage: Enable coverage reporting.
    """
    verbose_flag = "-v" if verbose else ""
    cov_flag = "--cov=src/nexus --cov-report=term-missing" if coverage else ""
    c.run(f"uv run pytest {verbose_flag} {cov_flag}")


@task
def test_ci(c: Context) -> None:
    """Run tests for CI with XML output.

    Args:
        c: Invoke context.
    """
    c.run(
        "uv run pytest --cov=src/nexus --cov-report=xml --cov-report=term-missing "
        "--junitxml=test-results.xml"
    )


# =============================================================================
# Linting & Formatting
# =============================================================================


@task
def ruff_check(c: Context, fix: bool = False) -> None:
    """Check code with ruff.

    Args:
        c: Invoke context.
        fix: Auto-fix issues.
    """
    print("Checking code with ruff...")
    fix_arg = "--fix --show-fixes" if fix else ""
    c.run(f"uv run ruff check src/ services/ scripts/ tasks.py {fix_arg}")


@task
def ruff_format(c: Context, check_only: bool = False) -> None:
    """Format code with ruff.

    Args:
        c: Invoke context.
        check_only: Only check format without making changes.
    """
    print("Formatting code with ruff...")
    check_arg = "--check" if check_only else ""
    c.run(f"uv run ruff format src/ services/ scripts/ tasks.py {check_arg}")


@task
def mypy(c: Context) -> None:
    """Run mypy type checking.

    Args:
        c: Invoke context.
    """
    print("Type checking with mypy...")
    c.run("uv run mypy src/ services/ tasks.py")


@task
def lint(c: Context) -> None:
    """Run all linting checks (ruff check, ruff format --check, mypy).

    Args:
        c: Invoke context.
    """
    ruff_check(c)
    ruff_format(c, check_only=True)
    mypy(c)


@task
def format(c: Context) -> None:
    """Format and fix all code issues.

    Args:
        c: Invoke context.
    """
    ruff_check(c, fix=True)
    ruff_format(c)


# =============================================================================
# Deployment Tasks
# =============================================================================


@task
def deploy(
    c: Context,
    services: Optional[str] = None,
    preset: Optional[str] = None,
    all_services: bool = False,
    skip_dns: bool = False,
    skip_ansible: bool = False,
    skip_cloudflared: bool = False,
    no_tunnel: bool = False,
    dry_run: bool = False,
    yes: bool = False,
) -> None:
    """Deploy Nexus services.

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
def restart(
    c: Context,
    services: Optional[str] = None,
    preset: Optional[str] = None,
    all_services: bool = False,
) -> None:
    """Quickly restart/redeploy services (skips DNS/Tunnel setup).

    Regenerates configurations and runs Ansible to apply changes/restart containers.
    Basically 'inv deploy' but faster.
    """
    deploy(
        c,
        services=services,
        preset=preset,
        all_services=all_services,
        skip_dns=True,
        skip_cloudflared=True,
        yes=True,
    )


# =============================================================================
# Health & Operations
# =============================================================================


@task
def health(c: Context, domain: Optional[str] = None, verbose: bool = False) -> None:
    """Run health checks.

    Args:
        c: Invoke context.
        domain: Base domain for SSL checks.
        verbose: Enable verbose output.
    """
    args = []
    if domain:
        args.append(f"--domain {domain}")
    if verbose:
        args.append("-v")
    c.run(f"uv run python -m nexus.cli.health {' '.join(args)}")


@task
def ops(
    c: Context,
    daily: bool = False,
    weekly: bool = False,
    monthly: bool = False,
    all_tasks: bool = False,
) -> None:
    """Run operations/maintenance tasks.

    Args:
        c: Invoke context.
        daily: Run daily tasks.
        weekly: Run weekly tasks.
        monthly: Run monthly tasks.
        all_tasks: Run all tasks.
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
def backup_list(c: Context) -> None:
    """List available backups.

    Args:
        c: Invoke context.
    """
    c.run("uv run python -m nexus.cli.restore --list")


@task
def backup_verify(c: Context, backup: Optional[str] = None) -> None:
    """Verify backup integrity.

    Args:
        c: Invoke context.
        backup: Specific backup to verify.
    """
    args = ["--verify"]
    if backup:
        args.append(f"--backup {backup}")
    c.run(f"uv run python -m nexus.cli.restore {' '.join(args)}")


@task
def restore(
    c: Context,
    backup: str = "",
    service: Optional[str] = None,
    dry_run: bool = False,
) -> None:
    """Restore from backup.

    Args:
        c: Invoke context.
        backup: Backup file to restore from.
        service: Specific service to restore.
        dry_run: Preview restore without executing.
    """
    args = [f"--backup {backup}"]
    if service:
        args.append(f"--service {service}")
    if dry_run:
        args.append("--dry-run")
    c.run(f"uv run python -m nexus.cli.restore {' '.join(args)}")


# =============================================================================
# Alert Bot
# =============================================================================


@task
def alert_bot(c: Context, port: int = 8080) -> None:
    """Run the Discord alert bot.

    Args:
        c: Invoke context.
        port: Port to run the webhook server on.
    """
    c.run(f"uv run python -m nexus.cli.alert_bot --port {port}")
