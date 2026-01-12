#!/bin/bash

# setup_model.sh
# Automates the creation/updating of the 'ena' Ollama model.

set -e

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
MODEL_FILE="$PROJECT_DIR/Modelfile"
MODEL_NAME="ena"
BASE_MODEL="qwen2.5:7b"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Starting Sure Finance Model Setup...${NC}"

# 1. Check if Ollama is installed
if ! command -v ollama &> /dev/null; then
    echo -e "${RED}Error: 'ollama' is not installed.${NC}"
    echo "Please install it from https://ollama.com/download/mac or via 'brew install --cask ollama'"
    exit 1
fi

# 2. Check if Ollama is running
if ! pgrep -x "ollama" > /dev/null && ! pgrep -x "Ollama" > /dev/null; then
    echo -e "${YELLOW}Ollama is not running. Starting it now...${NC}"
    # Start Ollama in the background (using 'serve' if CLI or opening App if Mac App)
    # Prefer opening the App on Mac to ensure system tray icon and proper context
    if [[ "$OSTYPE" == "darwin"* ]]; then
        open -a Ollama
    else
        ollama serve &
    fi
    
    # Wait for it to be ready
    echo "Waiting for Ollama to initialize..."
    while ! curl -s http://localhost:11434/api/tags > /dev/null; do
        sleep 1
    done
    echo -e "${GREEN}Ollama is running.${NC}"
else
    echo -e "${GREEN}Ollama is already running.${NC}"
fi

# 3. Pull the base model
echo -e "${YELLOW}Pulling base model ($BASE_MODEL)...${NC}"
ollama pull "$BASE_MODEL"

# 4. Create/Update the custom model
echo -e "${YELLOW}Creating/Updating '$MODEL_NAME' from Modelfile...${NC}"
if [ -f "$MODEL_FILE" ]; then
    ollama create "$MODEL_NAME" -f "$MODEL_FILE"
    echo -e "${GREEN}Successfully created '$MODEL_NAME'!${NC}"
else
    echo -e "${RED}Error: Modelfile not found at $MODEL_FILE${NC}"
    exit 1
fi

# 5. Quick Verification
echo -e "${YELLOW}Verifying model...${NC}"
RESPONSE=$(ollama run "$MODEL_NAME" "Categorize: Starbucks coffee $5.50" 2>/dev/null)

if [ $? -eq 0 ]; then
    echo -e "${GREEN}Verification passed. Model response:${NC}"
    echo "$RESPONSE"
    echo ""
    echo -e "${GREEN}Setup Complete!${NC}"
    echo "Ensure your sure/.env file has: SURE_OPENAI_MODEL=$MODEL_NAME"
else
    echo -e "${RED}Verification failed. Please check the logs.${NC}"
fi
