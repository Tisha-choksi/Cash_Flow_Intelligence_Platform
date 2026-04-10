#!/bin/bash

# Cash Flow Intelligence Platform - Development Setup Script
# Run this to setup the development environment

set -e  # Exit on error

echo "======================================================================"
echo "Cash Flow Intelligence Platform - Development Setup"
echo "======================================================================"

# Check Python version
echo "Checking Python version..."
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "Python version: $python_version"

if ! python3 -c 'import sys; exit(0 if sys.version_info >= (3, 10) else 1)'; then
    echo "Error: Python 3.10+ required"
    exit 1
fi

# Create virtual environment
echo ""
echo "Creating virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo ""
echo "Installing dependencies..."
pip install -r requirements.txt

# Copy environment file
echo ""
echo "Setting up environment configuration..."
if [ ! -f .env ]; then
    cp .env.example .env
    echo "Created .env file - please update with your settings"
else
    echo ".env file already exists"
fi

# Create database directories
echo ""
echo "Creating database directories..."
mkdir -p database
mkdir -p logs
mkdir -p migrations

# Install pre-commit hooks (optional)
if command -v pre-commit &> /dev/null; then
    echo ""
    echo "Installing pre-commit hooks..."
    pre-commit install
else
    echo "pre-commit not installed (optional)"
fi

echo ""
echo "======================================================================"
echo "Setup Complete!"
echo "======================================================================"
echo ""
echo "Next steps:"
echo "1. Update .env file with your database configuration"
echo "2. Start PostgreSQL (or use: docker-compose up db)"
echo "3. Run: python app/main.py"
echo "4. Visit: http://localhost:8000/api/docs"
echo ""
echo "Or use Docker:"
echo "  docker-compose up"
echo ""