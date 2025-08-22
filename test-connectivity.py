#!/usr/bin/env python3
"""
SET Portfolio API - Connectivity Test Script
Run this script from Windows to test connection to Mac-deployed application
"""

import requests
import sys
import time
from urllib.parse import urljoin

def test_connectivity(base_url):
    """Test connectivity to the SET Portfolio API"""
    
    print(f"🔍 Testing connectivity to: {base_url}")
    print("=" * 50)
    
    # Test endpoints
    endpoints = [
        ("/", "Main Dashboard"),
        ("/docs", "API Documentation"),
        ("/redoc", "Interactive API"),
        ("/api/health", "Health Check"),
    ]
    
    for endpoint, description in endpoints:
        url = urljoin(base_url, endpoint)
        print(f"\n📡 Testing {description}: {url}")
        
        try:
            start_time = time.time()
            response = requests.get(url, timeout=10)
            end_time = time.time()
            
            if response.status_code == 200:
                print(f"✅ SUCCESS - Status: {response.status_code} - Time: {end_time - start_time:.2f}s")
            else:
                print(f"⚠️  WARNING - Status: {response.status_code} - Time: {end_time - start_time:.2f}s")
                
        except requests.exceptions.ConnectionError:
            print("❌ ERROR - Connection refused (check if app is running)")
        except requests.exceptions.Timeout:
            print("❌ ERROR - Request timeout (check network)")
        except requests.exceptions.RequestException as e:
            print(f"❌ ERROR - {str(e)}")
    
    print("\n" + "=" * 50)
    print("🏁 Connectivity test completed!")

def main():
    """Main function"""
    print("SET Portfolio API - Connectivity Test")
    print("=====================================")
    print()
    
    # Get Mac IP address from user
    if len(sys.argv) > 1:
        mac_ip = sys.argv[1]
    else:
        mac_ip = input("Enter Mac's IP address (e.g., 192.168.1.100): ").strip()
    
    if not mac_ip:
        print("❌ No IP address provided!")
        sys.exit(1)
    
    # Construct base URL
    base_url = f"http://{mac_ip}:8000"
    
    # Test connectivity
    test_connectivity(base_url)
    
    print("\n📋 Next steps:")
    print(f"   🌐 Open browser: {base_url}")
    print(f"   📊 View API docs: {base_url}/docs")
    print(f"   🔧 If issues, check Mac deployment: docker-compose logs -f")

if __name__ == "__main__":
    main()
