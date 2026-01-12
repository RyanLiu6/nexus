from unittest.mock import patch

from nexus.deploy.auth import generate_authelia_config


@patch("nexus.deploy.auth.SERVICES_PATH")
def test_generate_authelia_config(mock_services_path, tmp_path):
    auth_dir = tmp_path / "auth"
    auth_dir.mkdir()

    mock_services_path.__truediv__.return_value = auth_dir
    mock_services_path.__truediv__.side_effect = lambda x: tmp_path / x

    sample_config = auth_dir / "configuration.yml.sample"
    sample_config.write_text("domain: example.com\nsome_key: value")

    generate_authelia_config("ryanliu6.xyz", dry_run=False)

    target_config = auth_dir / "configuration.yml"
    assert target_config.exists()
    content = target_config.read_text()
    assert "domain: ryanliu6.xyz" in content
    assert "some_key: value" in content


@patch("nexus.deploy.auth.SERVICES_PATH")
def test_generate_authelia_config_missing_sample(mock_services_path, tmp_path):
    mock_services_path.__truediv__.side_effect = lambda x: tmp_path / x

    generate_authelia_config("ryanliu6.xyz", dry_run=False)

    target_config = tmp_path / "auth" / "configuration.yml"
    assert not target_config.exists()
