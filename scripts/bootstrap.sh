#!/bin/bash
# Nexus Bootstrap Script
# Auto-installs dependencies for Nexus

set -e

echo "🚀 Nexus Bootstrap - Installing dependencies..."
echo ""

# Detect OS
if [[ "$OSTYPE" == "darwin"* ]]; then
    OS="macos"
    INSTALL_CMD="brew install"
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    OS="linux"
    INSTALL_CMD="sudo apt install -y"
else
    echo "❌ Unsupported OS: $OSTYPE"
    exit 1
fi

echo "📦 Detected OS: $OS"
echo ""

# Check for Python 3.9+
if command -v python3; then
    PYTHON_VERSION=$(python3 --version | cut -d. -f2 | cut -d. -f1)
    if (( $(echo "$PYTHON_VERSION < 3.9" | bc -l) )); then
        echo "❌ Python 3.9+ required, found: $PYTHON_VERSION"
        exit 1
    fi
    echo "✅ Python: $PYTHON_VERSION"
else
    echo "❌ Python 3.9+ not found"
    if [[ "$OS" == "macos" ]]; then
        brew install python@3.11
    else
        sudo apt install -y python3.11
    fi
fi

# Install uv if not present
if ! command -v uv; then
    echo "📦 Installing uv..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    echo "✅ uv installed"
else
    echo "✅ uv: $(uv --version)"
fi

# Install Docker if not present
if ! command -v docker; then
    echo "🐳 Installing Docker..."
    if [[ "$OS" == "macos" ]]; then
        brew install --cask docker
    else
        curl -fsSL https://get.docker.com -o get-docker.sh
        sudo sh get-docker.sh
        sudo usermod -aG docker $USER
    fi
    echo "✅ Docker installed"
else
    echo "✅ Docker: $(docker --version)"
fi

# Install Docker Compose if not present
if ! docker compose version &> /dev/null; then
    echo "🐳 Installing Docker Compose..."
    if [[ "$OS" == "macos" ]]; then
        brew install docker-compose
    else
        sudo apt install -y docker-compose-plugin
    fi
    echo "✅ Docker Compose installed"
else
    echo "✅ Docker Compose: $(docker compose version)"
fi

# Install Ansible if not present
if ! command -v ansible; then
    echo "🔧 Installing Ansible..."
    if [[ "$OS" == "macos" ]]; then
        brew install ansible
    else
        sudo apt install -y ansible
    fi
    echo "✅ Ansible installed: $(ansible --version)"
else
    echo "✅ Ansible: $(ansible --version)"
fi

# Install ansible-vault if not present
if ! command -v ansible-vault; then
    echo "🔐 Installing ansible-vault..."
    uv pip install ansible-vault
    echo "✅ ansible-vault installed"
else
    echo "✅ ansible-vault: $(ansible-vault --version)"
fi

# Install Terraform if not present
if ! command -v terraform; then
    echo "🏗️  Installing Terraform..."
    if [[ "$OS" == "macos" ]]; then
        brew install terraform
    else
        wget -O- https://apt.releases.hashicorp.com/terraform/pool/main/h/terraform_1.6.0_linux_amd64.zip
        unzip terraform_1.6.0_linux_amd64.zip
        sudo mv terraform /usr/local/bin/
        sudo chmod +x /usr/local/bin/terraform
        rm terraform_1.6.0_linux_amd64.zip
    fi
    echo "✅ Terraform installed: $(terraform version)"
else
    echo "✅ Terraform: $(terraform version)"
fi

# Create data directories
echo ""
echo "📁 Creating data directories..."
mkdir -p "$HOME/dev/focus"
mkdir -p "$HOME/nexus-backups"
mkdir -p "$HOME/dev/focus/services/auth/config"
mkdir -p "$HOME/dev/focus/services/dashboard/config"
mkdir -p "$HOME/dev/focus/services/traefik/rules"
echo "✅ Data directories created"

# Install Python dependencies
echo ""
echo "🐍 Installing Python dependencies..."
uv pip install -e ".[dev]"
echo "✅ Python dependencies installed"

echo ""
echo "🎉 Bootstrap complete!"
echo ""
echo "Next steps:"
echo "  1. Generate secrets: ./scripts/generate-secrets.sh"
echo "  2. Encrypt vault: ansible-vault encrypt ansible/vars/vault.yml"
echo "  3. Deploy services: ./scripts/deploy.py -p home"
echo ""
