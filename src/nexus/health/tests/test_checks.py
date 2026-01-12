from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from nexus.health.checks import (
    ServiceHealth,
    check_all_services,
    check_disk_space,
    check_docker_containers,
    check_service_health,
    check_ssl_certificates,
)


class TestServiceHealth:
    def test_init(self):
        service = ServiceHealth("traefik", "https://traefik.example.com")

        assert service.name == "traefik"
        assert service.url == "https://traefik.example.com"
        assert service.healthy is False
        assert service.status_code is None
        assert service.response_time is None
        assert service.error is None


class TestCheckServiceHealth:
    @pytest.mark.asyncio
    async def test_check_service_health_success(self):
        service = ServiceHealth("test", "https://test.example.com")
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=None)

        mock_session = MagicMock()
        mock_session.get = MagicMock(return_value=mock_response)

        await check_service_health(service, mock_session)

        assert service.healthy is True
        assert service.status_code == 200
        assert service.response_time is not None

    @pytest.mark.asyncio
    async def test_check_service_health_http_error(self):
        service = ServiceHealth("test", "https://test.example.com")
        mock_response = MagicMock()
        mock_response.status = 500
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=None)

        mock_session = MagicMock()
        mock_session.get = MagicMock(return_value=mock_response)

        await check_service_health(service, mock_session)

        assert service.healthy is False
        assert service.status_code == 500

    @pytest.mark.asyncio
    async def test_check_service_health_client_error(self):
        service = ServiceHealth("test", "https://test.example.com")
        mock_response = MagicMock()
        mock_response.status = 404
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=None)

        mock_session = MagicMock()
        mock_session.get = MagicMock(return_value=mock_response)

        await check_service_health(service, mock_session)

        assert service.healthy is True
        assert service.error == "HTTP 404"

    @pytest.mark.asyncio
    async def test_check_service_health_timeout(self):
        service = ServiceHealth("test", "https://test.example.com")
        mock_session = MagicMock()
        mock_session.get = MagicMock(side_effect=TimeoutError())

        await check_service_health(service, mock_session)

        assert service.healthy is False
        assert service.error == "Timeout"

    @pytest.mark.asyncio
    async def test_check_service_health_exception(self):
        service = ServiceHealth("test", "https://test.example.com")
        mock_session = MagicMock()
        mock_session.get = MagicMock(side_effect=Exception("Connection refused"))

        await check_service_health(service, mock_session)

        assert service.healthy is False
        assert "Connection refused" in service.error


class TestCheckAllServices:
    @pytest.mark.asyncio
    async def test_check_all_services(self):
        services = [
            ServiceHealth("svc1", "https://svc1.example.com"),
            ServiceHealth("svc2", "https://svc2.example.com"),
        ]

        with patch(
            "nexus.health.checks.check_service_health", new_callable=AsyncMock
        ) as mock_check:
            await check_all_services(services)
            assert mock_check.call_count == 2


class TestCheckDockerContainers:
    def test_check_docker_containers_healthy(self):
        mock_result = MagicMock()
        mock_result.stdout = "traefik\tUp 2 days (healthy)\nnginx\tUp 1 hour"

        with patch("subprocess.run", return_value=mock_result):
            result = check_docker_containers()

        assert result["traefik"] is True
        assert result["nginx"] is False

    def test_check_docker_containers_empty(self):
        mock_result = MagicMock()
        mock_result.stdout = ""

        with patch("subprocess.run", return_value=mock_result):
            result = check_docker_containers()

        assert result == {}

    def test_check_docker_containers_malformed(self):
        mock_result = MagicMock()
        mock_result.stdout = "traefik\tUp 2 days (healthy)\nmalformed line"

        with patch("subprocess.run", return_value=mock_result):
            result = check_docker_containers()

        assert "traefik" in result


class TestCheckDiskSpace:
    def test_check_disk_space_success(self):
        # total, used, free in bytes
        # 100GB = 100 * 1024 * 1024 * 1024 = 107374182400
        # 50GB used
        # 50GB free
        mock_usage = (107374182400, 53687091200, 53687091200)

        with patch("shutil.disk_usage", return_value=mock_usage):
            result = check_disk_space()

        assert result["total"] == "100.0G"
        assert result["used"] == "50.0G"
        assert result["available"] == "50.0G"
        assert result["usage_percent"] == "50%"

    def test_check_disk_space_error(self):
        with patch("shutil.disk_usage", side_effect=OSError("Disk error")):
            result = check_disk_space()

        assert result == {}


class TestCheckSslCertificates:
    def test_check_ssl_certificates_success(self):
        mock_socket = MagicMock()
        mock_ssl_socket = MagicMock()
        mock_ssl_socket.getpeercert.return_value = {"subject": "test"}
        mock_context = MagicMock()
        mock_context.wrap_socket.return_value.__enter__ = MagicMock(
            return_value=mock_ssl_socket
        )
        mock_context.wrap_socket.return_value.__exit__ = MagicMock(return_value=None)

        with (
            patch("socket.create_connection") as mock_create_conn,
            patch("ssl.create_default_context", return_value=mock_context),
        ):
            mock_create_conn.return_value.__enter__ = MagicMock(
                return_value=mock_socket
            )
            mock_create_conn.return_value.__exit__ = MagicMock(return_value=None)

            result = check_ssl_certificates("example.com")

        assert "traefik" in result
        assert "grafana" in result
        assert "prometheus" in result

    def test_check_ssl_certificates_failure(self):
        with patch(
            "socket.create_connection", side_effect=Exception("Connection refused")
        ):
            result = check_ssl_certificates("example.com")

        assert result.get("traefik") is False

    def test_check_ssl_certificates_exception(self):
        with patch(
            "socket.create_connection", side_effect=Exception("Connection error")
        ):
            result = check_ssl_certificates("example.com")

        assert "traefik" in result
        assert result["traefik"] is False
