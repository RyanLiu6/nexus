#!/bin/bash
# Nexus Tailscale SSH Setup Script
# Sets up Tailscale SSH for secure, keyless SSH access (especially for mobile devices)

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
log_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# Check if script is running as root
check_root() {
    if [[ $EUID -ne 0 ]]; then
        log_error "This script must be run as root (sudo)"
        log_info "Run with: sudo $0"
        exit 1
    fi
}

# Check operating system
check_os() {
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        OS="linux"
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        OS="macos"
    else
        log_error "Unsupported operating system: $OSTYPE"
        exit 1
    fi
    log_info "Detected OS: $OS"
}

# Check if Tailscale is installed
check_tailscale() {
    log_info "Checking Tailscale installation..."

    if ! command -v tailscale &> /dev/null; then
        log_error "Tailscale is not installed"
        log_info "Install Tailscale:"
        log_info "  Linux:   curl -fsSL https://tailscale.com/install.sh | sh"
        log_info "  macOS:   brew install --cask tailscale"
        exit 1
    fi

    log_success "Tailscale is installed"
}

# Check if Tailscale is connected
check_tailscale_status() {
    log_info "Checking Tailscale status..."

    local status=$(tailscale status --json 2>/dev/null)

    if echo "$status" | grep -q '"BackendState":"Running"'; then
        log_success "Tailscale is connected"
        TAILSCALE_IP=$(echo "$status" | grep -o '"TailscaleIPs":\[[^]]*\]' | grep -o '[0-9.]*' | head -1)
        MACHINE_NAME=$(echo "$status" | grep -o '"Self":{[^}]*}' | grep -o '"Name":"[^"]*"' | cut -d'"' -f4)
        log_info "Machine Name: $MACHINE_NAME"
        log_info "Tailscale IP: $TAILSCALE_IP"
    else
        log_error "Tailscale is not connected"
        log_info "Please login first: sudo tailscale up"
        exit 1
    fi
}

# Enable Tailscale SSH
enable_tailscale_ssh() {
    log_info "Enabling Tailscale SSH..."

    tailscale up --ssh 2>/dev/null || true

    # Verify SSH is enabled
    sleep 2
    local ssh_enabled=$(tailscale status --json 2>/dev/null | grep -o '"SSH":true')

    if [[ -n "$ssh_enabled" ]]; then
        log_success "Tailscale SSH is enabled"
    else
        log_error "Failed to enable Tailscale SSH"
        log_info "Manual steps:"
        log_info "  1. Run: sudo tailscale up --ssh"
        log_info "  2. Check status: tailscale status --json | grep SSH"
        exit 1
    fi
}

# Configure SSH server for Tailscale
configure_sshd() {
    log_info "Configuring SSH server for Tailscale..."

    local sshd_config="/etc/ssh/sshd_config"

    # Backup original config
    if [[ ! -f "${sshd_config}.bak" ]]; then
        cp "$sshd_config" "${sshd_config}.bak"
        log_info "Backed up SSH config to ${sshd_config}.bak"
    fi

    # Check if Tailscale SSH configuration exists
    if grep -q "tailscale" "$sshd_config"; then
        log_warning "Tailscale SSH config already exists in sshd_config"
        return 0
    fi

    # Add Tailscale SSH configuration
    cat >> "$sshd_config" <<'EOF'

# Tailscale SSH configuration
Match Address *,100.64.0.0/10,fd7a:115c:a1e0::/96,127.0.0.0/8,::1/128
    AuthenticationMethods publickey
    PermitRootLogin prohibit-password
EOF

    # Restart SSH server
    if [[ "$OS" == "linux" ]]; then
        systemctl restart sshd 2>/dev/null || systemctl restart ssh 2>/dev/null
        log_success "SSH server restarted (Linux)"
    elif [[ "$OS" == "macos" ]]; then
        brew services restart openssh 2>/dev/null || log_warning "Could not restart SSH on macOS (may need manual restart)"
        log_info "Manual restart: sudo launchctl stop com.openssh.sshd && sudo launchctl start com.openssh.sshd"
    fi

    log_success "SSH server configured for Tailscale"
}

# Display ACL configuration
display_acl_config() {
    log_info "Tailscale ACL Configuration Required"
    echo
    log_warning "You must configure Tailscale ACLs to allow SSH access"
    echo
    echo "1. Go to: https://login.tailscale.com/admin/acls"
    echo "2. Add the following to your ACL configuration:"
    echo
    echo '```json'
    echo '{'
    echo '  "tagOwners": {'
    echo "    \"tag:nexus-admin\": [\"group:admins\"],"
    echo "    \"tag:nexus-user\": [\"group:users\"]"
    echo '  },'
    echo '  "acls": ['
    echo '    {'
    echo '      "action": "accept",'
    echo '      "src": ["group:admins"],'
    echo '      "dst": ["tag:nexus-admin:*", "autogroup:internet:*"]'
    echo '    },'
    echo '    {'
    echo '      "action": "accept",'
    echo '      "src": ["group:users"],'
    echo '      "dst": ["tag:nexus-user:*", "autogroup:internet:*"]'
    echo '    },'
    echo '    {'
    echo '      "action": "check",'
    echo '      "src": ["*"],'
    echo '      "dst": ["autogroup:internet:*"],'
    echo '      "users": ["*"],'
    echo '      "checkPeriod": "21600h"'
    echo '    }'
    echo '  ]'
    echo '}'
    echo '```'
    echo
    log_info "After updating ACLs, assign tags to this server:"
    echo "  sudo tailscale set --tags=tag:nexus-admin"
    echo
}

# Assign tag to device
assign_tag() {
    local tag="${1:-tag:nexus-admin}"

    log_info "Assigning tag: $tag"

    tailscale set --tags="$tag" 2>/dev/null || true

    # Verify tag was assigned
    sleep 2
    local current_tags=$(tailscale status --json 2>/dev/null | grep -o '"Tags":\[[^]]*\]' | grep -o '"[^"]*"' | tr '\n' ' ')

    if echo "$current_tags" | grep -q "$tag"; then
        log_success "Tag assigned: $tag"
    else
        log_warning "Could not verify tag assignment"
        log_info "You may need to approve the tag in Tailscale admin console"
    fi
}

# Test SSH connection
test_ssh() {
    log_info "Testing Tailscale SSH..."

    if ssh -o ConnectTimeout=10 -o StrictHostKeyChecking=no \
        -o PreferredAuthentications=publickey \
        -o IdentitiesOnly=yes \
        root@"$TAILSCALE_IP" \
        "echo 'Tailscale SSH connection successful!'" 2>/dev/null; then

        log_success "Tailscale SSH connection test passed!"
    else
        log_warning "SSH connection test failed (may require ACL configuration)"
        log_info "This is normal if ACLs haven't been configured yet"
        log_info "After configuring ACLs, test with:"
        echo "  ssh root@$TAILSCALE_IP"
        echo "  ssh root@$MACHINE_NAME.tailnet-name.ts.net"
    fi
}

# Show mobile setup instructions
show_mobile_instructions() {
    echo
    log_info "Mobile Device Setup Instructions"
    echo
    echo "iOS Devices:"
    echo "  1. Install Tailscale app: https://apps.apple.com/app/tailscale/id1474447279"
    echo "  2. Login to your Tailscale account"
    echo "  3. Enable VPN"
    echo "  4. Open Tailscale app → Find this server → Tap 'SSH'"
    echo "  5. Or use Termius app with: ssh root@$MACHINE_NAME.tailnet-name.ts.net"
    echo
    echo "Android Devices:"
    echo "  1. Install Tailscale app: https://play.google.com/store/apps/details?id=com.tailscale.ipn"
    echo "  2. Login to your Tailscale account"
    echo "  3. Enable VPN"
    echo "  4. Open Tailscale app → Find this server → Tap 'SSH'"
    echo "  5. Or use Termius app with: ssh root@$MACHINE_NAME.tailnet-name.ts.net"
    echo
    log_info "Desktop Devices (macOS/Linux/Windows):"
    echo "  ssh root@$MACHINE_NAME.tailnet-name.ts.net"
    echo "  ssh root@$TAILSCALE_IP"
    echo
}

# Show next steps
show_next_steps() {
    echo
    log_info "Next Steps:"
    echo
    echo "1. Configure Tailscale ACLs (see instructions above)"
    echo "   Go to: https://login.tailscale.com/admin/acls"
    echo
    echo "2. Verify ACL configuration allows your user/group to SSH"
    echo
    echo "3. Test SSH from another device:"
    echo "   ssh root@$MACHINE_NAME.tailnet-name.ts.net"
    echo
    echo "4. For traditional SSH access, run:"
    echo "   ./scripts/setup-ssh.sh user@server-ip"
    echo
    echo "5. Documentation: docs/SSH_ACCESS.md"
    echo
}

# Show usage
show_usage() {
    echo "Usage: sudo $0 [options]"
    echo
    echo "Options:"
    echo "  --tag            Tag to assign (default: tag:nexus-admin)"
    echo "  --skip-sshd      Skip SSH server configuration"
    echo "  --skip-test      Skip SSH connection test"
    echo "  --help           Show this help message"
    echo
    echo "Examples:"
    echo "  sudo $0"
    echo "  sudo $0 --tag tag:nexus-user"
    echo "  sudo $0 --skip-sshd"
    echo
}

# Main function
main() {
    local tag="tag:nexus-admin"
    local skip_sshd=false
    local skip_test=false

    # Parse arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            --tag)
                tag="$2"
                shift 2
                ;;
            --skip-sshd)
                skip_sshd=true
                shift
                ;;
            --skip-test)
                skip_test=true
                shift
                ;;
            --help)
                show_usage
                exit 0
                ;;
            *)
                log_error "Unknown option: $1"
                show_usage
                exit 1
                ;;
        esac
    done

    # Run setup
    log_info "Starting Nexus Tailscale SSH setup..."
    echo

    check_root
    check_os
    check_tailscale
    check_tailscale_status
    enable_tailscale_ssh

    if [[ "$skip_sshd" == false ]]; then
        configure_sshd
    else
        log_info "Skipping SSH server configuration (--skip-sshd flag)"
    fi

    assign_tag "$tag"
    display_acl_config

    if [[ "$skip_test" == false ]]; then
        test_ssh
    else
        log_info "Skipping SSH connection test (--skip-test flag)"
    fi

    show_mobile_instructions
    show_next_steps

    log_success "Nexus Tailscale SSH setup complete!"
}

# Run main function
main "$@"
