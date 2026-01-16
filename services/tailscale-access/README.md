# Tailscale Access Control Service

This service provides group-based access control for Nexus services behind Traefik. It acts as a ForwardAuth middleware.

## How It Works

1.  **Traefik** receives a request for `service.domain.com`.
2.  It forwards the request to this service (`tailscale-access`).
3.  **tailscale-access**:
    *   Extracts the client IP from `X-Forwarded-For`.
    *   Queries the local Tailscale socket (`/var/run/tailscale/tailscaled.sock`) to identify the user.
    *   Loads access rules from `access-rules.yml`.
    *   Checks if the user belongs to a group allowed to access the service.
4.  **Result**:
    *   **Allowed**: Returns 200 OK. Adds `Remote-User` and `Remote-Groups` headers.
    *   **Denied**: Returns 403 Forbidden with a friendly HTML page explaining why.

## Configuration

*   **Rules**: `/config/access-rules.yml` (mounted from host)
*   **Tailscale Socket**: `/var/run/tailscale/tailscaled.sock` (mounted from host)

## Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run locally (needs mock or real tailscale socket)
export ACCESS_RULES_PATH=../../tailscale/access-rules.yml
export DEV_MODE=true
python main.py
```
