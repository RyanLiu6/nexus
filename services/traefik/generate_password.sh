#!/bin/bash

SUDO=''
if [ "$EUID" -ne 0 ]; then SUDO='sudo'; fi

echo "Basic auth for traefik >= v1.7"
read -p "User: " USER
read -s -p "Password: " PW
echo

# Checks if htpasswd is available or install it otherwise
if ! which htpasswd >/dev/null; then
    $SUDO apt-get update && $SUDO apt-get install -y apache2-utils
fi

# Generate strings
echo "------- Your raw password string --------"
string=$(htpasswd -nbB "$USER" "$PW")
echo "$string"
echo "------- Your string for docker-compose.yml --------"
# Escape string
escaped_string=$(echo "$string" | sed -e 's/\$/\$\$/g')
echo "$escaped_string"
