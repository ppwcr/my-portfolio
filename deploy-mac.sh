#!/bin/bash

# SET Portfolio API - Mac Deployment Script
# This script deploys the application on Mac for external access

echo "========================================"
echo "SET Portfolio API - Mac Deployment"
echo "========================================"
echo ""

# Check if Docker is installed and running
if ! command -v docker &> /dev/null; then
    echo "❌ ERROR: Docker is not installed!"
    echo "Please install Docker Desktop for Mac and start it."
    exit 1
fi

if ! docker info &> /dev/null; then
    echo "❌ ERROR: Docker is not running!"
    echo "Please start Docker Desktop for Mac."
    exit 1
fi

echo "✓ Docker is available and running"
echo ""

# Create necessary directories
mkdir -p _out out_set_sectors

# Get Mac's IP address
MAC_IP=$(ifconfig | grep "inet " | grep -v 127.0.0.1 | head -1 | awk '{print $2}')
echo "📱 Your Mac's IP address: $MAC_IP"
echo ""

# Ask user for deployment type
echo "Choose deployment type:"
echo "1. Local network access (same network)"
echo "2. External access (different networks)"
echo "3. Cloud deployment (production)"
echo ""

read -p "Enter your choice (1-3): " choice

case $choice in
    1)
        echo ""
        echo "🚀 Deploying for local network access..."
        echo "Other devices on the same network can access:"
        echo "   http://$MAC_IP:8000"
        echo ""
        
        docker-compose up --build -d
        
        echo "✅ Application deployed successfully!"
        echo "🌐 Access URL: http://$MAC_IP:8000"
        echo "📊 API Docs: http://$MAC_IP:8000/docs"
        ;;
        
    2)
        echo ""
        echo "🚀 Deploying for external access..."
        echo "⚠️  Note: You may need to configure port forwarding on your router"
        echo ""
        
        docker-compose -f docker-compose-mac.yml up --build -d
        
        echo "✅ Application deployed successfully!"
        echo "🌐 Access URL: http://$MAC_IP:8000"
        echo "📊 API Docs: http://$MAC_IP:8000/docs"
        echo ""
        echo "🔧 To allow external access, you may need to:"
        echo "   1. Configure port forwarding on your router (port 8000)"
        echo "   2. Configure your Mac's firewall"
        echo "   3. Use your public IP address instead of local IP"
        ;;
        
    3)
        echo ""
        echo "🚀 Deploying for cloud production..."
        echo "⚠️  Make sure to set up environment variables first!"
        echo ""
        
        if [ ! -f .env ]; then
            echo "❌ .env file not found!"
            echo "Please copy env.template to .env and configure your settings."
            exit 1
        fi
        
        docker-compose -f docker-compose-cloud.yml up --build -d
        
        echo "✅ Application deployed successfully!"
        echo "🌐 Access URL: http://$MAC_IP:8000"
        echo "📊 API Docs: http://$MAC_IP:8000/docs"
        echo ""
        echo "🔧 For production, consider:"
        echo "   1. Setting up SSL/HTTPS"
        echo "   2. Using a domain name"
        echo "   3. Setting up monitoring and logging"
        ;;
        
    *)
        echo "❌ Invalid choice. Please run the script again."
        exit 1
        ;;
esac

echo ""
echo "📋 Useful commands:"
echo "   View logs: docker-compose logs -f"
echo "   Stop app:  docker-compose down"
echo "   Restart:   docker-compose restart"
echo ""
echo "🔍 To check if the app is running:"
echo "   curl http://localhost:8000/"
echo ""
