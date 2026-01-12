#!/bin/bash
# Nexus SSH Key Setup Script
# Sets up traditional SSH key-based authentication for Nexus server access

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

# Check if script is running on Linux/macOS
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

# Check dependencies
check_dependencies() {
    log_info "Checking dependencies..."

    local missing_deps=()

    command -v ssh-keygen >/dev/null 2>&1 || missing_deps+=("ssh-keygen")
    command -v ssh-copy-id >/dev/null 2>&1 || missing_deps+=("ssh-copy-id")

    if [[ ${#missing_deps[@]} -gt 0 ]]; then
        log_error "Missing dependencies: ${missing_deps[*]}"
        log_info "Install with: sudo apt install openssh-client (Ubuntu/Debian)"
        log_info "Or: sudo yum install openssh-clients (RHEL/CentOS)"
        exit 1
    fi

    log_success "All dependencies found"
}

# Generate SSH key pair
generate_key() {
    local key_name="${1:-nexus}"
    local key_path="$HOME/.ssh/${key_name}"
    local email="${2:-nexus@example.com}"
    local key_type="${3:-ed25519}"

    log_info "Generating SSH key pair..."

    # Check if key already exists
    if [[ -f "$key_path" ]]; then
        log_warning "Key already exists at: $key_path"
        read -p "Overwrite existing key? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            log_info "Using existing key"
            return 0
        fi
        rm -f "$key_path" "$key_path.pub"
    fi

    # Generate key
    case "$key_type" in
        ed25519)
            ssh-keygen -t ed25519 -C "$email" -f "$key_path"
            ;;
        rsa)
            ssh-keygen -t rsa -b 4096 -C "$email" -f "$key_path"
            ;;
        *)
            log_error "Unsupported key type: $key_type"
            log_info "Supported types: ed25519, rsa"
            exit 1
            ;;
    esac

    # Set correct permissions
    chmod 600 "$key_path"
    chmod 644 "$key_path.pub"

    log_success "SSH key generated: $key_path"
}

# Copy public key to server
copy_key_to_server() {
    local server="$1"
    local key_name="${2:-nexus}"
    local key_path="$HOME/.ssh/${key_name}"

    log_info "Copying public key to server: $server"

    # Check if key exists
    if [[ ! -f "$key_path" ]]; then
        log_error "Key not found: $key_path"
        exit 1
    fi

    # Copy key using ssh-copy-id
    ssh-copy-id -i "$key_path.pub" "$server"

    log_success "Public key copied to server"
}

# Configure SSH client
configure_ssh_config() {
    local server="$1"
    local key_name="${2:-nexus}"
    local key_path="$HOME/.ssh/${key_name}"
    local config_file="$HOME/.ssh/config"
    local alias_name="${3:-nexus}"

    log_info "Configuring SSH client..."

    # Create config file if it doesn't exist
    if [[ ! -f "$config_file" ]]; then
        touch "$config_file"
        chmod 600 "$config_file"
    fi

    # Extract hostname from server string (user@hostname)
    local hostname=$(echo "$server" | cut -d'@' -f2)
    local username=$(echo "$server" | cut -d'@' -f1)

    # Check if alias already exists
    if grep -q "^Host ${alias_name}$" "$config_file"; then
        log_warning "Host alias '$alias_name' already exists in $config_file"
        read -p "Update existing configuration? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            log_info "Skipping SSH config update"
            return 0
        fi
        # Remove existing entry
        sed -i.bak "/^Host ${alias_name}$/,/^$/d" "$config_file" 2>/dev/null || \
        gsed -i.bak "/^Host ${alias_name}$/,/^$/d" "$config_file" 2>/dev/null || \
        log_warning "Could not remove existing entry (manual update required)"
    fi

    # Add configuration
    cat >> "$config_file" <<EOF

# Nexus Homelab Server
Host ${alias_name}
    HostName ${hostname}
    User ${username}
    IdentityFile ${key_path}
    PreferredAuthentications publickey
    IdentitiesOnly yes
    ServerAliveInterval 60
    ServerAliveCountMax 3

EOF

    log_success "SSH config updated: $config_file"
    log_info "You can now connect with: ssh ${alias_name}"
}

# Test SSH connection
test_connection() {
    local alias_name="${1:-nexus}"

    log_info "Testing SSH connection..."

    if ssh -o ConnectTimeout=10 -o StrictHostKeyChecking=no "$alias_name" "echo 'SSH connection successful!'"; then
        log_success "SSH connection test passed!"
        log_info "You can now connect with: ssh ${alias_name}"
    else
        log_error "SSH connection test failed!"
        log_info "Please check:"
        log_info "  1. Server is reachable"
        log_info "  2. SSH server is running on server"
        log_info "  3. Firewall allows SSH (port 22)"
        log_info "  4. Public key was copied correctly"
        exit 1
    fi
}

# Display public key
display_public_key() {
    local key_name="${1:-nexus}"
    local key_path="$HOME/.ssh/${key_name}.pub"

    log_info "Public key:"
    echo
    cat "$key_path"
    echo
}

# Show next steps
show_next_steps() {
    local alias_name="${1:-nexus}"
    echo
    log_info "Next steps:"
    echo "  1. Connect to server: ssh ${alias_name}"
    echo "  2. Configure SSH server hardening (optional):"
    echo "     sudo vi /etc/ssh/sshd_config"
    echo "  3. Restart SSH server:"
    echo "     sudo systemctl restart sshd  # Linux"
    echo "     sudo brew services restart openssh  # macOS"
    echo "  4. For mobile access, consider Tailscale SSH: ./scripts/setup-tailscale-ssh.sh"
    echo
}

# Show usage
show_usage() {
    echo "Usage: $0 [user@server] [options]"
    echo
    echo "Arguments:"
    echo "  user@server      Server address (e.g., user@192.168.1.50)"
    echo
    echo "Options:"
    echo "  -k, --key-name   Name of SSH key (default: nexus)"
    echo "  -e, --email      Email for key comment (default: nexus@example.com)"
    echo "  -t, --type       Key type: ed25519 or rsa (default: ed25519)"
    echo "  -a, --alias      SSH alias name (default: nexus)"
    echo "  --skip-config    Skip SSH config update"
    echo "  --skip-test      Skip connection test"
    echo "  --no-copy        Skip copying key to server (manual copy)"
    echo "  -h, --help       Show this help message"
    echo
    echo "Examples:"
    echo "  $0 user@192.168.1.50"
    echo "  $0 user@nexus.local -k my-nexus-key"
    echo "  $0 user@192.168.1.50 -a myserver -t rsa"
    echo
}

# Main function
main() {
    local server=""
    local key_name="nexus"
    local email="nexus@example.com"
    local key_type="ed25519"
    local alias_name="nexus"
    local skip_config=false
    local skip_test=false
    local no_copy=false

    # Parse arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            -k|--key-name)
                key_name="$2"
                shift 2
                ;;
            -e|--email)
                email="$2"
                shift 2
                ;;
            -t|--type)
                key_type="$2"
                shift 2
                ;;
            -a|--alias)
                alias_name="$2"
                shift 2
                ;;
            --skip-config)
                skip_config=true
                shift
                ;;
            --skip-test)
                skip_test=true
                shift
                ;;
            --no-copy)
                no_copy=true
                shift
                ;;
            -h|--help)
                show_usage
                exit 0
                ;;
            -*)
                log_error "Unknown option: $1"
                show_usage
                exit 1
                ;;
            *)
                server="$1"
                shift
                ;;
        esac
    done

    # Validate server address
    if [[ -z "$server" ]] && [[ "$no_copy" == false ]]; then
        log_error "Server address required (use --no-copy to skip server connection)"
        show_usage
        exit 1
    fi

    # Run setup
    log_info "Starting Nexus SSH setup..."
    echo

    check_os
    check_dependencies
    generate_key "$key_name" "$email" "$key_type"

    if [[ "$no_copy" == false ]]; then
        copy_key_to_server "$server" "$key_name"
    else
        log_info "Skipping key copy to server (--no-copy flag)"
        display_public_key "$key_name"
        log_info "Copy the public key above to: $server:~/.ssh/authorized_keys"
        echo
    fi

    if [[ "$skip_config" == false ]]; then
        configure_ssh_config "$server" "$key_name" "$alias_name"
    else
        log_info "Skipping SSH config update (--skip-config flag)"
    fi

    if [[ "$skip_test" == false ]] && [[ "$no_copy" == false ]]; then
        test_connection "$alias_name"
    else
        log_info "Skipping connection test (--skip-test or --no-copy flag)"
    fi

    show_next_steps "$alias_name"

    log_success "Nexus SSH setup complete!"
}

# Run main function
main "$@"
