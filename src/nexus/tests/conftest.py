from pathlib import Path
from typing import Generator
from unittest.mock import MagicMock, patch

import pytest


@pytest.fixture
def temp_services_path(tmp_path: Path) -> Path:
    services_dir = tmp_path / "services"
    services_dir.mkdir()

    for service in ["traefik", "auth", "dashboard", "plex", "jellyfin"]:
        service_dir = services_dir / service
        service_dir.mkdir()
        compose_file = service_dir / "docker-compose.yml"
        compose_file.write_text(f"""services:
  {service}:
    image: {service}:latest
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.{service}.rule=Host(`{service}.example.com`)"
""")

    return services_dir


@pytest.fixture
def mock_env_vars(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("NEXUS_DOMAIN", "example.com")
    monkeypatch.setenv("NEXUS_ROOT_DIRECTORY", "/tmp/nexus")
    monkeypatch.setenv("DATA_DIRECTORY", "/tmp/data")
    monkeypatch.setenv("TZ", "UTC")


@pytest.fixture
def mock_subprocess() -> Generator[MagicMock, None, None]:
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="",
            stderr="",
        )
        yield mock_run


@pytest.fixture
def temp_ansible_path(tmp_path: Path) -> Path:
    ansible_dir = tmp_path / "ansible"
    ansible_dir.mkdir()

    playbook = ansible_dir / "playbook.yml"
    playbook.write_text("""---
- name: Test playbook
  hosts: localhost
  tasks: []
""")

    vars_dir = ansible_dir / "vars"
    vars_dir.mkdir()

    return ansible_dir


@pytest.fixture
def temp_terraform_path(tmp_path: Path) -> Path:
    tf_dir = tmp_path / "terraform"
    tf_dir.mkdir()

    main_tf = tf_dir / "main.tf"
    main_tf.write_text("""
terraform {
  required_providers {
    cloudflare = {
      source  = "cloudflare/cloudflare"
      version = "~> 4.0"
    }
  }
}
""")

    return tf_dir
