from pathlib import Path
from unittest.mock import patch

import yaml

from nexus.generate.access_rules import generate_access_rules, sync_access_rules


class TestGenerateAccessRules:
    def test_generates_dict(self) -> None:
        rules = generate_access_rules()
        assert isinstance(rules, dict)
        assert "services" in rules
        assert "default" in rules

    def test_default_is_deny(self) -> None:
        rules = generate_access_rules()
        assert rules["default"] == "deny"

    def test_services_have_groups(self) -> None:
        rules = generate_access_rules()
        for _name, config in rules["services"].items():
            assert "groups" in config
            assert isinstance(config["groups"], list)

    def test_filters_by_service_list(self) -> None:
        # Only request dashboard
        rules = generate_access_rules(services=["dashboard"])
        # Should have dashboard-related entries
        service_names = list(rules["services"].keys())
        # Dashboard maps to "nexus" subdomain
        assert "nexus" in service_names or "dashboard" in service_names

    def test_writes_to_output_path(self, tmp_path: Path) -> None:
        output_path = tmp_path / "access-rules.yml"

        generate_access_rules(output_path=output_path)

        assert output_path.exists()
        content = output_path.read_text()
        # Should have header comment
        assert "AUTO-GENERATED" in content
        # Should be valid YAML
        parsed = yaml.safe_load(content)
        assert "services" in parsed


class TestSyncAccessRules:
    def test_sync_creates_file(self, tmp_path: Path) -> None:
        with patch("nexus.generate.access_rules.TAILSCALE_PATH", tmp_path):
            sync_access_rules()

            # Check file was created
            expected_path = tmp_path / "access-rules.yml"
            assert expected_path.exists()
