import http.client
import json
import os
import socket

import yaml
from flask import Flask, Response, render_template, request

app = Flask(__name__)

# Configuration
ACCESS_RULES_PATH = os.environ.get("ACCESS_RULES_PATH", "/config/access-rules.yml")
TAILSCALE_SOCKET_PATH = os.environ.get(
    "TAILSCALE_SOCKET", "/var/run/tailscale/tailscaled.sock"
)


def load_rules():
    """Load access rules from the configured YAML file.

    Returns:
        dict: The parsed access rules containing groups and service permissions.
            Returns an empty dict if the file cannot be loaded.
    """
    try:
        with open(ACCESS_RULES_PATH) as f:
            return yaml.safe_load(f)
    except Exception as e:
        print(f"Error loading rules: {e}")
        return {}


def get_service_from_host(host):
    """Extract the service name from the hostname.

    Args:
        host: The full hostname (e.g., "grafana.example.com").

    Returns:
        str: The subdomain/service name (e.g., "grafana").
    """
    if not host:
        return "unknown"
    # host usually looks like "service.domain.com" or "service"
    # We want the first part
    return host.split(".")[0]


class UnixSocketConnection(http.client.HTTPConnection):
    def __init__(self, socket_path):
        super().__init__("localhost")
        self.socket_path = socket_path

    def connect(self):
        self.sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.sock.connect(self.socket_path)


def get_tailscale_user(ip):
    """Query the local Tailscale API to identify the user behind an IP address.

    Args:
        ip: The source IP address of the request.

    Returns:
        dict: The user profile containing 'LoginName' and 'DisplayName',
              or None if lookup fails.
    """
    # If developing locally without tailscale, return a mock user if configured
    if os.environ.get("DEV_MODE") == "true":
        return {"LoginName": "dev@example.com", "DisplayName": "Dev User"}

    try:
        conn = UnixSocketConnection(TAILSCALE_SOCKET_PATH)
        conn.request("GET", f"/localapi/v0/whois?addr={ip}")
        resp = conn.getresponse()

        if resp.status != 200:
            print(f"Tailscale API error: {resp.status} {resp.reason}")
            return None

        data = json.loads(resp.read().decode())
        # The API returns a structure like:
        # {
        #   "Node": { ... },
        #   "UserProfile": { "LoginName": "user@gmail.com", ... },
        #   "CapMap": { ... }
        # }
        return data.get("UserProfile")
    except Exception as e:
        print(f"Error querying Tailscale: {e}")
        return None


def get_user_groups(email, rules):
    """Determine which groups a user belongs to based on their email.

    Args:
        email: The user's email address.
        rules: The loaded access rules configuration.

    Returns:
        list: A list of group names the user belongs to.
    """
    user_groups = []
    groups_config = rules.get("groups", {})

    for group_name, members in groups_config.items():
        if email in members:
            user_groups.append(group_name)

    return user_groups


@app.route("/auth")
def auth():
    """Handle authentication requests from Traefik ForwardAuth.

    1. Identifies the target service from the Host header.
    2. Identifies the user via Tailscale LocalAPI using the source IP.
    3. Checks if the user's groups permit access to the service.
    4. Returns 200 OK with identity headers if authorized, or 403 Forbidden.
    """
    # 1. Get Service
    host = request.headers.get("X-Forwarded-Host", "")
    service = get_service_from_host(host)

    # 2. Get User Identity
    # Traefik passes the client IP in X-Forwarded-For.
    # The real client IP is usually the first one if there's a list.
    client_ip = request.headers.get("X-Forwarded-For", "").split(",")[0].strip()

    if not client_ip:
        return render_template("403.html", reason="No Client IP", service=service), 403

    user_profile = get_tailscale_user(client_ip)

    if not user_profile:
        # If we can't identify the user via Tailscale, deny access
        # This implies the user isn't coming from Tailscale or the API is broken
        return render_template(
            "403.html",
            reason="Not a Tailscale connection",
            service=service,
            ip=client_ip,
        ), 403

    user_email = user_profile.get("LoginName")

    # 3. Check Access
    rules = load_rules()
    user_groups = get_user_groups(user_email, rules)

    service_rules = rules.get("services", {}).get(service, {})
    if not service_rules:
        # Check default behavior
        default_action = rules.get("default", "deny")
        if default_action != "allow":
            return render_template(
                "403.html",
                reason=f"Service '{service}' not configured",
                user={"email": user_email, "groups": user_groups},
                service=service,
            ), 403
    else:
        allowed_groups = service_rules.get("groups", [])
        # Check if user has ANY of the allowed groups
        has_access = any(group in allowed_groups for group in user_groups)

        if not has_access:
            return render_template(
                "403.html",
                reason="Access Denied",
                user={"email": user_email, "groups": user_groups},
                service=service,
                required_groups=allowed_groups,
            ), 403

    # 4. Authorized
    response = Response("OK", 200)
    # Pass user info to downstream service via headers
    response.headers["Remote-User"] = user_email
    response.headers["Remote-Groups"] = ",".join(user_groups)
    response.headers["Remote-Name"] = user_profile.get("DisplayName", "")

    return response


@app.route("/health")
def health():
    """Health check endpoint for container orchestration.

    Returns:
        tuple: A 200 OK response indicating the service is healthy.
    """
    return "OK", 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
