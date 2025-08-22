# Windows Access Guide - SET Portfolio API

This guide explains how to access the SET Portfolio API when it's deployed on a Mac from a Windows machine.

## 🌐 Access Methods

### Method 1: Same Network Access (Recommended)

**Prerequisites:**
- Both Mac and Windows machines are on the same WiFi/network
- Application is deployed on Mac using the deployment script

**Steps:**

1. **On Mac - Deploy the application:**
   ```bash
   # Run the deployment script
   ./deploy-mac.sh
   
   # Choose option 1: Local network access
   ```

2. **Get Mac's IP address:**
   - The deployment script will show the IP address
   - Or run on Mac: `ifconfig | grep "inet " | grep -v 127.0.0.1`

3. **On Windows - Access the application:**
   - Open any web browser (Chrome, Firefox, Edge)
   - Go to: `http://[MAC_IP_ADDRESS]:8000`
   - Example: `http://192.168.1.100:8000`

4. **Available endpoints:**
   - Main Dashboard: `http://[MAC_IP]:8000/`
   - API Documentation: `http://[MAC_IP]:8000/docs`
   - Interactive API: `http://[MAC_IP]:8000/redoc`

### Method 2: Different Networks (Port Forwarding)

**Prerequisites:**
- Mac is on one network, Windows on another
- Router supports port forwarding

**Steps:**

1. **On Mac - Deploy for external access:**
   ```bash
   ./deploy-mac.sh
   # Choose option 2: External access
   ```

2. **Configure router port forwarding:**
   - Access your router's admin panel
   - Set up port forwarding: External port 8000 → Mac's IP:8000
   - Note your public IP address

3. **On Windows - Access via public IP:**
   - Go to: `http://[PUBLIC_IP]:8000`
   - Example: `http://203.xxx.xxx.xxx:8000`

### Method 3: Cloud Deployment

**Prerequisites:**
- Application deployed to cloud service (AWS, Google Cloud, etc.)
- Domain name (optional but recommended)

**Steps:**

1. **Deploy to cloud:**
   ```bash
   ./deploy-mac.sh
   # Choose option 3: Cloud deployment
   ```

2. **Access from Windows:**
   - Use the cloud service URL
   - Example: `https://your-app.herokuapp.com`

## 🔧 Troubleshooting

### Connection Issues

1. **"Connection refused" error:**
   - Check if Mac's firewall is blocking port 8000
   - Ensure Docker container is running: `docker ps`
   - Verify port is exposed: `docker port set-portfolio-api`

2. **"Page not found" error:**
   - Check if application is running: `curl http://localhost:8000/`
   - View container logs: `docker-compose logs -f`

3. **Slow connection:**
   - Check network speed between devices
   - Consider using a wired connection for better performance

### Security Considerations

1. **Local Network:**
   - Generally safe for home/office networks
   - Avoid on public WiFi without VPN

2. **External Access:**
   - Use HTTPS when possible
   - Consider setting up authentication
   - Monitor access logs

3. **Cloud Deployment:**
   - Always use HTTPS
   - Set up proper authentication
   - Use environment variables for secrets

## 📱 Mobile Access

You can also access the application from mobile devices:

1. **iOS/Android:**
   - Open mobile browser
   - Go to: `http://[MAC_IP]:8000`
   - The interface is responsive and mobile-friendly

2. **Mobile App:**
   - The project includes a React Native mobile app
   - Update the API endpoint in the mobile app configuration

## 🛠️ Advanced Configuration

### Custom Port

If you want to use a different port:

1. **On Mac - Modify docker-compose.yml:**
   ```yaml
   ports:
     - "8080:8000"  # Use port 8080 instead of 8000
   ```

2. **On Windows - Access with new port:**
   - Go to: `http://[MAC_IP]:8080`

### SSL/HTTPS Setup

For secure access:

1. **Generate SSL certificate:**
   ```bash
   # On Mac
   openssl req -x509 -newkey rsa:4096 -keyout key.pem -out cert.pem -days 365 -nodes
   ```

2. **Use nginx reverse proxy:**
   - Use the `docker-compose-cloud.yml` configuration
   - Configure SSL certificates

3. **Access via HTTPS:**
   - Go to: `https://[MAC_IP]:443`

## 📊 Monitoring and Logs

### Check Application Status

**On Mac:**
```bash
# Check if container is running
docker ps

# View application logs
docker-compose logs -f

# Check application health
curl http://localhost:8000/health
```

### Performance Monitoring

**On Windows:**
- Use browser developer tools to monitor network requests
- Check response times in browser Network tab
- Monitor memory and CPU usage if needed

## 🔄 Updates and Maintenance

### Update Application

1. **On Mac:**
   ```bash
   # Pull latest changes
   git pull
   
   # Rebuild and restart
   docker-compose down
   docker-compose up --build -d
   ```

2. **On Windows:**
   - Refresh browser to see updates
   - Clear browser cache if needed

### Backup Data

**On Mac:**
```bash
# Backup data directories
tar -czf backup_$(date +%Y%m%d).tar.gz _out/ out_set_sectors/
```

## 📞 Support

If you encounter issues:

1. **Check logs:** `docker-compose logs -f`
2. **Restart container:** `docker-compose restart`
3. **Rebuild container:** `docker-compose up --build -d`
4. **Check network:** `ping [MAC_IP]` from Windows

## 🎯 Quick Reference

| Action | Mac Command | Windows Access |
|--------|-------------|----------------|
| Deploy | `./deploy-mac.sh` | `http://[MAC_IP]:8000` |
| View logs | `docker-compose logs -f` | Browser DevTools |
| Restart | `docker-compose restart` | Refresh browser |
| Stop | `docker-compose down` | Connection lost |
| Update | `git pull && docker-compose up --build -d` | Refresh browser |
