# SET Portfolio API - Docker Deployment Guide

This guide explains how to deploy the SET Portfolio API using Docker on Windows.

## Prerequisites

1. **Docker Desktop**
   - **Windows**: Download from [Docker Desktop](https://www.docker.com/products/docker-desktop/)
   - **Mac**: Download from [Docker Desktop for Mac](https://www.docker.com/products/docker-desktop/)
   - Ensure Docker Desktop is running
   - Enable WSL 2 backend (Windows, recommended)

2. **Git** (optional, for cloning the repository)

## Cross-Platform Deployment

### Deploy on Mac, Access from Windows

You can deploy the application on Mac and access it from Windows machines:

1. **On Mac - Deploy the application:**
   ```bash
   # Run the Mac deployment script
   ./deploy-mac.sh
   
   # Choose deployment type:
   # 1. Local network access (same network)
   # 2. External access (different networks)
   # 3. Cloud deployment (production)
   ```

2. **On Windows - Test connectivity:**
   ```bash
   # Run the connectivity test
   test-connectivity.bat [MAC_IP_ADDRESS]
   
   # Or manually test in browser:
   # http://[MAC_IP_ADDRESS]:8000
   ```

3. **Access the application:**
   - Main Dashboard: `http://[MAC_IP]:8000/`
   - API Documentation: `http://[MAC_IP]:8000/docs`
   - Interactive API: `http://[MAC_IP]:8000/redoc`

See `WINDOWS_ACCESS_GUIDE.md` for detailed cross-platform access instructions.

## Quick Start

### Option 1: Using Docker Compose (Recommended)

1. **Clone or download the project**
   ```bash
   git clone <repository-url>
   cd my-portfolio
   ```

2. **Run the application**
   ```bash
   # Double-click the batch file
   docker-compose-run.bat
   
   # Or use command line
   docker-compose up
   ```

3. **Access the application**
   - Open your browser and go to: http://localhost:8000
   - The API documentation is available at: http://localhost:8000/docs

### Option 2: Using Docker directly

1. **Build and run using the batch file**
   ```bash
   # Double-click the batch file
   docker-build-and-run.bat
   ```

2. **Or use command line**
   ```bash
   # Build the image
   docker build -t set-portfolio-api .
   
   # Run the container
   docker run --rm -p 8000:8000 -v "%cd%\_out:/app/_out" -v "%cd%\out_set_sectors:/app/out_set_sectors" set-portfolio-api
   ```

## Environment Configuration

### Setting up Environment Variables

1. **Create a `.env` file** in the project root:
   ```env
   SUPABASE_URL=your_supabase_url_here
   SUPABASE_KEY=your_supabase_key_here
   ```

2. **Update docker-compose.yml** to include your environment variables:
   ```yaml
   environment:
     - SUPABASE_URL=your_supabase_url
     - SUPABASE_KEY=your_supabase_key
   ```

### Database Setup

1. **Set up Supabase database** using the provided SQL files:
   - `create_portfolio_holdings_table.sql`
   - `create_set_index_table.sql`

2. **Run the setup script** (if needed):
   ```bash
   docker run --rm -v "%cd%:/app" set-portfolio-api python setup_portfolio_table.py
   ```

## Docker Commands Reference

### Basic Commands

```bash
# Build the image
docker build -t set-portfolio-api .

# Run in foreground
docker run --rm -p 8000:8000 set-portfolio-api

# Run in background
docker run -d --name set-portfolio-api -p 8000:8000 set-portfolio-api

# Stop and remove container
docker stop set-portfolio-api
docker rm set-portfolio-api
```

### Docker Compose Commands

```bash
# Start services
docker-compose up

# Start in background
docker-compose up -d

# Stop services
docker-compose down

# View logs
docker-compose logs -f

# Rebuild and start
docker-compose up --build

# Stop and remove everything
docker-compose down -v
```

### Volume Management

The application uses Docker volumes to persist data:

- `./_out` - Downloaded Excel files and reports
- `./out_set_sectors` - Sector data exports

These directories are automatically created and mounted to preserve data between container restarts.

## Troubleshooting

### Common Issues

1. **Port 8000 already in use**
   ```bash
   # Change the port in docker-compose.yml
   ports:
     - "8001:8000"  # Use port 8001 instead
   ```

2. **Permission denied errors**
   - Ensure Docker Desktop has access to the project directory
   - Run Docker Desktop as Administrator if needed

3. **Playwright browser issues**
   - The Dockerfile includes all necessary dependencies for Playwright
   - If you encounter browser-related errors, rebuild the image:
   ```bash
   docker-compose build --no-cache
   ```

4. **Memory issues**
   - Increase Docker Desktop memory allocation (recommended: 4GB+)
   - Go to Docker Desktop Settings > Resources > Memory

### Logs and Debugging

```bash
# View container logs
docker logs set-portfolio-api

# Follow logs in real-time
docker logs -f set-portfolio-api

# Execute commands in running container
docker exec -it set-portfolio-api bash

# Check container status
docker ps
```

## Production Deployment

### Security Considerations

1. **Environment Variables**: Never commit `.env` files to version control
2. **Network Security**: Use reverse proxy (nginx) for production
3. **SSL/TLS**: Configure HTTPS in production
4. **Resource Limits**: Set appropriate CPU and memory limits

### Example Production docker-compose.yml

```yaml
version: '3.8'

services:
  set-portfolio-api:
    build: .
    container_name: set-portfolio-api-prod
    ports:
      - "8000:8000"
    environment:
      - PYTHONUNBUFFERED=1
      - SUPABASE_URL=${SUPABASE_URL}
      - SUPABASE_KEY=${SUPABASE_KEY}
    volumes:
      - ./_out:/app/_out
      - ./out_set_sectors:/app/out_set_sectors
    restart: unless-stopped
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 2G
        reservations:
          cpus: '1.0'
          memory: 1G
    networks:
      - set-portfolio-network

networks:
  set-portfolio-network:
    driver: bridge
```

## Performance Optimization

1. **Multi-stage builds**: Consider using multi-stage Dockerfile for smaller images
2. **Caching**: Use Docker layer caching effectively
3. **Resource allocation**: Monitor and adjust CPU/memory limits
4. **Database connection pooling**: Configure appropriate connection limits

## Support

For issues related to:
- **Docker**: Check Docker Desktop logs and documentation
- **Application**: Check the main README.md file
- **Database**: Refer to Supabase documentation

## File Structure

```
my-portfolio/
├── Dockerfile                 # Docker image definition
├── docker-compose.yml         # Docker Compose configuration
├── .dockerignore             # Files to exclude from Docker build
├── docker-build-and-run.bat  # Windows batch script for Docker
├── docker-compose-run.bat    # Windows batch script for Docker Compose
├── requirements.txt          # Python dependencies
├── main.py                   # Main FastAPI application
├── _out/                     # Data output directory (mounted volume)
├── out_set_sectors/          # Sector data directory (mounted volume)
└── templates/                # HTML templates
```
