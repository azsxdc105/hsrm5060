#!/bin/bash
# Build script for Render.com deployment

echo "🚀 Starting build process..."

# Install dependencies
echo "📦 Installing dependencies..."
pip install -r requirements_production.txt

# Create necessary directories
echo "📁 Creating directories..."
mkdir -p /tmp/uploads
mkdir -p /tmp/backups
mkdir -p /tmp/logs

# Set permissions
chmod 755 /tmp/uploads
chmod 755 /tmp/backups
chmod 755 /tmp/logs

echo "✅ Build completed successfully!"