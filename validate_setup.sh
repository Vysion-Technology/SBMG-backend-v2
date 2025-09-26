#!/bin/bash

# SBM Rajasthan Application Validation Script
# This script validates that the Docker setup is working correctly

set -e

echo "🔍 SBM Rajasthan Application Validation"
echo "======================================"

# Check if Docker is installed
echo "📦 Checking Docker installation..."
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker and try again."
    exit 1
fi
echo "✅ Docker is installed"

# Check if Docker Compose is available
echo "📦 Checking Docker Compose..."
if ! docker compose version &> /dev/null; then
    echo "❌ Docker Compose is not available. Please install Docker Compose and try again."
    exit 1
fi
echo "✅ Docker Compose is available"

# Check if docker-compose.yml exists
echo "📄 Checking configuration files..."
if [ ! -f "docker-compose.yml" ]; then
    echo "❌ docker-compose.yml not found. Please run this script from the project root."
    exit 1
fi
echo "✅ Docker Compose configuration found"

# Validate Docker Compose configuration
echo "🔧 Validating Docker Compose configuration..."
if ! docker compose config --quiet; then
    echo "❌ Docker Compose configuration is invalid."
    exit 1
fi
echo "✅ Docker Compose configuration is valid"

# Check if backend Dockerfile exists
echo "📄 Checking Dockerfile..."
if [ ! -f "backend/Dockerfile" ]; then
    echo "❌ backend/Dockerfile not found."
    exit 1
fi
echo "✅ Backend Dockerfile found"

echo ""
echo "🎉 Validation completed successfully!"
echo ""
echo "🚀 To start the application:"
echo "   docker compose up -d"
echo ""
echo "📚 To view API documentation:"
echo "   Open http://localhost:8000/docs in your browser"
echo ""
echo "🔐 Default admin credentials:"
echo "   Username: admin"
echo "   Password: admin123"
echo "   (Change these in production!)"
echo ""
echo "🔧 To initialize default data:"
echo "   python init_app.py"
echo ""