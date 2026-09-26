#!/bin/bash
set -e

echo "🚀 Installing Scrypted natively on macOS..."

# Check for Homebrew
if ! command -v brew &> /dev/null; then
    echo "❌ Homebrew is required but not installed."
    echo "Please install it with: /bin/bash -c \"\$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\""
    exit 1
fi

TEMP_SCRIPT="$(mktemp "${HOME}/install-scrypted-XXXXXX.sh")"
trap 'rm -f "${TEMP_SCRIPT}"' EXIT INT TERM

echo "📥 Downloading Scrypted macOS installation script..."
curl -fsSL https://raw.githubusercontent.com/koush/scrypted/main/install/local/install-scrypted-dependencies-mac.sh > "${TEMP_SCRIPT}"

echo "⚙️ Running installation script..."
bash "${TEMP_SCRIPT}"

echo ""
echo "✅ Scrypted installation complete!"
echo "🌐 Access the dashboard at: https://localhost:10443/"
echo "Note: Scrypted uses a self-signed certificate. You'll need to bypass the browser security warning."
