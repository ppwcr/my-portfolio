#!/bin/bash

# Vercel Deployment Script for SET Portfolio App

echo "🚀 Starting Vercel deployment for SET Portfolio App..."

# Check if Vercel CLI is installed
if ! command -v vercel &> /dev/null; then
    echo "❌ Vercel CLI not found. Installing..."
    npm install -g vercel
fi

# Check if user is logged in
if ! vercel whoami &> /dev/null; then
    echo "🔐 Please login to Vercel..."
    vercel login
fi

# Check if we're in a git repository
if ! git rev-parse --git-dir > /dev/null 2>&1; then
    echo "❌ Not in a git repository. Please initialize git first:"
    echo "   git init"
    echo "   git add ."
    echo "   git commit -m 'Initial commit'"
    exit 1
fi

# Check if all required files exist
required_files=("main_vercel.py" "requirements-vercel.txt" "vercel.json" "runtime.txt")
for file in "${required_files[@]}"; do
    if [ ! -f "$file" ]; then
        echo "❌ Required file not found: $file"
        exit 1
    fi
done

echo "✅ All required files found"

# Check if environment variables are set
if [ -z "$SUPABASE_URL" ] || [ -z "$SUPABASE_KEY" ]; then
    echo "⚠️  Warning: Environment variables not set locally"
    echo "   Make sure to set them in Vercel dashboard:"
    echo "   - SUPABASE_URL"
    echo "   - SUPABASE_KEY"
fi

# Deploy to Vercel
echo "📦 Deploying to Vercel..."
if [ "$1" = "--prod" ]; then
    echo "🎯 Deploying to production..."
    vercel --prod
else
    echo "🧪 Deploying to preview..."
    vercel
fi

echo "✅ Deployment completed!"
echo ""
echo "📋 Next steps:"
echo "1. Set environment variables in Vercel dashboard"
echo "2. Test your application"
echo "3. Configure custom domain (optional)"
echo "4. Set up monitoring and alerts"
echo ""
echo "📚 For more information, see VERCEL_DEPLOYMENT.md"
