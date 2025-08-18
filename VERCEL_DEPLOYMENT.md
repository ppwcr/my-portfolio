# Vercel Production Deployment Guide

This guide will help you deploy your SET Portfolio application to Vercel for production.

## Prerequisites

1. **Vercel Account**: Sign up at [vercel.com](https://vercel.com)
2. **Vercel CLI**: Install with `npm i -g vercel`
3. **Git Repository**: Your code should be in a Git repository

## Deployment Steps

### 1. Install Vercel CLI
```bash
npm install -g vercel
```

### 2. Login to Vercel
```bash
vercel login
```

### 3. Deploy to Vercel
```bash
vercel --prod
```

Or for the first deployment:
```bash
vercel
```

### 4. Environment Variables Setup

After deployment, you'll need to set up environment variables in the Vercel dashboard:

1. Go to your project in the Vercel dashboard
2. Navigate to Settings > Environment Variables
3. Add the following variables:

```
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_anon_key
```

### 5. Verify Deployment

Your application will be available at:
- Production: `https://your-project-name.vercel.app`
- Preview: `https://your-project-name-git-branch.vercel.app`

## Key Changes for Vercel

### 1. Serverless Optimizations
- **File System**: Uses `/tmp` directory for temporary files
- **State Management**: No persistent file storage
- **Dependencies**: Removed Playwright (not supported on Vercel)

### 2. Disabled Features
- Excel file downloads (requires Playwright)
- Browser automation
- Persistent file storage

### 3. Enabled Features
- Stock data via yfinance
- Portfolio management
- Real-time data updates
- Web scraping (basic)

## Configuration Files

### vercel.json
```json
{
  "version": 2,
  "builds": [
    {
      "src": "main_vercel.py",
      "use": "@vercel/python"
    }
  ],
  "routes": [
    {
      "src": "/(.*)",
      "dest": "main_vercel.py"
    }
  ],
  "functions": {
    "main_vercel.py": {
      "maxDuration": 300
    }
  }
}
```

### requirements-vercel.txt
Vercel-compatible dependencies without Playwright.

### runtime.txt
Specifies Python 3.11 for Vercel.

## API Endpoints

### Available Endpoints
- `GET /` - Main dashboard
- `GET /portfolio` - Portfolio page
- `GET /api/health` - Health check
- `GET /api/symbol/{symbol}` - Stock data
- `GET /api/portfolio` - Portfolio data
- `POST /api/portfolio/update-symbol-data/{symbol}` - Update symbol data
- `GET /api/status` - Application status

### Disabled Endpoints
- Excel download endpoints (Playwright dependency)

## Monitoring and Debugging

### 1. Vercel Dashboard
- Function logs
- Performance metrics
- Error tracking

### 2. Health Check
```bash
curl https://your-app.vercel.app/api/health
```

### 3. Status Check
```bash
curl https://your-app.vercel.app/api/status
```

## Custom Domain (Optional)

1. Go to Vercel dashboard > Settings > Domains
2. Add your custom domain
3. Configure DNS records as instructed

## Troubleshooting

### Common Issues

1. **Import Errors**: Check that all dependencies are in `requirements-vercel.txt`
2. **Timeout Errors**: Increase `maxDuration` in `vercel.json`
3. **Environment Variables**: Ensure all required env vars are set in Vercel dashboard
4. **File System Errors**: Use `/tmp` directory for temporary files

### Debug Commands

```bash
# Check deployment status
vercel ls

# View function logs
vercel logs

# Redeploy
vercel --prod
```

## Performance Optimization

1. **Caching**: Implement Redis or similar for data caching
2. **CDN**: Vercel provides global CDN automatically
3. **Database**: Use Supabase for persistent data storage
4. **API Limits**: Be mindful of yfinance API rate limits

## Security Considerations

1. **Environment Variables**: Never commit secrets to Git
2. **API Keys**: Use Vercel's environment variable system
3. **CORS**: Configure CORS if needed for your frontend
4. **Rate Limiting**: Implement rate limiting for API endpoints

## Next Steps

1. Set up monitoring and alerting
2. Configure custom domain
3. Set up CI/CD pipeline
4. Implement caching strategy
5. Add authentication if needed

## Support

- [Vercel Documentation](https://vercel.com/docs)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Python on Vercel](https://vercel.com/docs/runtimes#official-runtimes/python)
