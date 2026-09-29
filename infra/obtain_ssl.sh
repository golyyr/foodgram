#!/bin/bash
# Получает доверенный Let's Encrypt сертификат для nip.io.
set -euo pipefail

DOMAIN="${1:-158-160-159-158.nip.io}"
EMAIL="${2:-subbotin_antoshka@mail.ru}"
ROOT="$(cd "$(dirname "$0")" && pwd)"
SSL_DIR="$ROOT/ssl"
WEBROOT="$ROOT/certbot/www"
CONF_DIR="$ROOT/certbot/conf"

mkdir -p "$SSL_DIR" "$WEBROOT" "$CONF_DIR"

if [ ! -f "$SSL_DIR/foodgram.crt" ] || [ ! -f "$SSL_DIR/foodgram.key" ]; then
  openssl req -x509 -nodes -newkey rsa:2048 -days 3 \
    -keyout "$SSL_DIR/foodgram.key" \
    -out "$SSL_DIR/foodgram.crt" \
    -subj "/CN=$DOMAIN"
fi

cd "$ROOT"
sudo docker compose up -d --no-build nginx

# HTTP-01: challenge раздаётся с порта 80 из ./certbot/www
sudo docker run --rm \
  -v "$CONF_DIR:/etc/letsencrypt" \
  -v "$WEBROOT:/var/www/certbot" \
  certbot/certbot certonly \
  --webroot -w /var/www/certbot \
  -d "$DOMAIN" \
  --email "$EMAIL" \
  --agree-tos \
  --no-eff-email \
  --non-interactive \
  --preferred-challenges http

sudo cp "$CONF_DIR/live/$DOMAIN/fullchain.pem" "$SSL_DIR/foodgram.crt"
sudo cp "$CONF_DIR/live/$DOMAIN/privkey.pem" "$SSL_DIR/foodgram.key"
sudo chmod 644 "$SSL_DIR/foodgram.crt"
sudo chmod 600 "$SSL_DIR/foodgram.key"

sudo docker compose exec -T nginx nginx -s reload
echo "HTTPS ready: https://$DOMAIN"
