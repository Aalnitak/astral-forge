#!/usr/bin/env bash
set -e pipefail

echo "Finding Caddy local root certificate..."
CERT_PATH="$(docker compose exec -T caddy find ../data -name root.crt | head -n 1 | tr -d '\r')"

if [ -z "$CERT_PATH" ]; then
  echo "Could not find root.crt inside the Caddy container."
  echo "Make sure Caddy is running."
  exit 1
fi

echo "Caddy root certificate found at: $CERT_PATH"
echo "Copying certificate to host machine..."
docker compose cp "caddy:$CERT_PATH" ./caddy-root.crt
echo "Certificate copied to ./caddy-root.crt"
echo "Trusting Caddy root certificate on macOS..."
sudo security add-trusted-cert -d -r trustRoot -k /Library/Keychains/System.keychain ./caddy-root.crt
echo "Caddy root certificate trusted successfully."
echo "Restart browser to apply changes."