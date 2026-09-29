#!/bin/bash
set -euo pipefail

SSL_DIR="$(cd "$(dirname "$0")" && pwd)/ssl"
mkdir -p "$SSL_DIR"

openssl req -x509 -nodes -newkey rsa:2048 -days 825 \
  -keyout "$SSL_DIR/foodgram.key" \
  -out "$SSL_DIR/foodgram.crt" \
  -subj "/CN=158.160.159.158" \
  -addext "subjectAltName=IP:158.160.159.158,DNS:158.160.159.158"

chmod 600 "$SSL_DIR/foodgram.key"
chmod 644 "$SSL_DIR/foodgram.crt"
echo "SSL certificate created in $SSL_DIR"
