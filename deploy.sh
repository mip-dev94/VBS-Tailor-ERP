#!/bin/bash
set -e

echo "=== VBS Tailor ERP - Deploy ==="

# Check Docker
if ! command -v docker &> /dev/null; then
    echo "Installing Docker..."
    curl -fsSL https://get.docker.com | sh
    sudo usermod -aG docker $USER
    echo "Docker installed. Please log out and back in, then re-run this script."
    exit 1
fi

# Create .env if not exists
if [ ! -f .env ]; then
    cp .env.example .env
    echo "Created .env from .env.example — edit passwords before production!"
fi

# Build and start
echo "Building and starting containers..."
docker compose up -d --build

echo ""
echo "=== Deploy complete ==="
echo "Odoo:  http://$(hostname -I | awk '{print $1}'):${ODOO_PORT:-8069}"
echo ""
echo "First time? Initialize database:"
echo "  docker compose exec odoo odoo -i vbs_planning,vbs_erp --stop-after-init"
echo ""
echo "Logs:  docker compose logs -f odoo"
