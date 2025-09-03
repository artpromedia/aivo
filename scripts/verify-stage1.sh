#!/bin/bash

# Stage-1 Compose Setup and Verification Script

set -e

echo "🚀 Stage-1 Docker Compose Setup and Verification"
echo "================================================"

# Change to the repository root
cd "$(dirname "$0")/.."

echo "📦 Starting all S1 services with Docker Compose..."
docker compose -f infra/compose/local.yml up -d

echo "⏳ Waiting for services to be ready..."
sleep 30

echo "🔍 Running golden path verification..."
if command -v node &> /dev/null; then
    node scripts/verify-stage1.js
elif command -v ts-node &> /dev/null; then
    ts-node scripts/verify-stage1.ts
else
    echo "❌ Neither node nor ts-node found. Please install Node.js or ts-node."
    exit 1
fi

echo "✅ Stage-1 setup and verification complete!"
echo "🌐 Services are running on:"
echo "  - Kong Gateway: http://localhost:8000"
echo "  - Admin Portal API: http://localhost:8091"
echo "  - MailHog (Email UI): http://localhost:8025"
echo ""
echo "📊 To view logs: docker compose -f infra/compose/local.yml logs -f [service]"
echo "🛑 To stop: docker compose -f infra/compose/local.yml down"
