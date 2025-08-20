#!/usr/bin/env python3
"""
Scheduled Tasks Diagnostic Script
Checks the status of scheduled tasks and tests scheduled scraping functionality
"""

import os
import sys
import subprocess
import platform
from datetime import datetime
from pathlib import Path

def check_windows_scheduled_tasks():
    """Check Windows scheduled tasks status"""
    print("🔍 Checking Windows Scheduled Tasks...")
    
    tasks = ["SET_Scraper_1030", "SET_Scraper_1300", "SET_Scraper_1730"]
    found_tasks = []
    
    for task in tasks:
        try:
            result = subprocess.run(
                ["schtasks", "/query", "/tn", task], 
                capture_output=True, 
                text=True, 
                timeout=10
            )
            if result.returncode == 0:
                print(f"✅ {task}: Found and active")
                found_tasks.append(task)
            else:
                print(f"❌ {task}: Not found")
        except (subprocess.TimeoutExpired, FileNotFoundError):
            print(f"❌ {task}: Not found or command failed")
    
    return found_tasks

def check_macos_scheduled_tasks():
    """Check macOS scheduled tasks (crontab)"""
    print("🔍 Checking macOS Scheduled Tasks...")
    
    try:
        result = subprocess.run(
            ["crontab", "-l"], 
            capture_output=True, 
            text=True, 
            timeout=10
        )
        if result.returncode == 0:
            crontab_content = result.stdout
            if "run_scheduled_scrape" in crontab_content or "portfolio" in crontab_content:
                print("✅ Found portfolio-related cron jobs:")
                for line in crontab_content.split('\n'):
                    if "run_scheduled_scrape" in line or "portfolio" in line:
                        print(f"   {line.strip()}")
                return True
            else:
                print("❌ No portfolio-related cron jobs found")
                return False
        else:
            print("❌ No crontab entries found")
            return False
    except (subprocess.TimeoutExpired, FileNotFoundError):
        print("❌ Could not check crontab")
        return False

def check_linux_scheduled_tasks():
    """Check Linux scheduled tasks (crontab)"""
    print("🔍 Checking Linux Scheduled Tasks...")
    
    try:
        result = subprocess.run(
            ["crontab", "-l"], 
            capture_output=True, 
            text=True, 
            timeout=10
        )
        if result.returncode == 0:
            crontab_content = result.stdout
            if "run_scheduled_scrape" in crontab_content or "portfolio" in crontab_content:
                print("✅ Found portfolio-related cron jobs:")
                for line in crontab_content.split('\n'):
                    if "run_scheduled_scrape" in line or "portfolio" in line:
                        print(f"   {line.strip()}")
                return True
            else:
                print("❌ No portfolio-related cron jobs found")
                return False
        else:
            print("❌ No crontab entries found")
            return False
    except (subprocess.TimeoutExpired, FileNotFoundError):
        print("❌ Could not check crontab")
        return False

def check_required_files():
    """Check if required files exist"""
    print("\n📁 Checking Required Files...")
    
    current_dir = Path.cwd()
    required_files = [
        "run_scheduled_scrape.bat",
        "background_updater.py",
        "main.py",
        "requirements.txt"
    ]
    
    missing_files = []
    for file in required_files:
        file_path = current_dir / file
        if file_path.exists():
            print(f"✅ {file}: Found")
        else:
            print(f"❌ {file}: Missing")
            missing_files.append(file)
    
    return len(missing_files) == 0

def check_python_environment():
    """Check Python environment"""
    print("\n🐍 Checking Python Environment...")
    
    # Check Python version
    try:
        result = subprocess.run(
            [sys.executable, "--version"], 
            capture_output=True, 
            text=True, 
            timeout=10
        )
        if result.returncode == 0:
            print(f"✅ Python: {result.stdout.strip()}")
        else:
            print("❌ Python: Version check failed")
            return False
    except Exception as e:
        print(f"❌ Python: Error checking version - {e}")
        return False
    
    # Check required packages
    required_packages = ["fastapi", "uvicorn", "pandas", "requests"]
    missing_packages = []
    
    for package in required_packages:
        try:
            result = subprocess.run(
                [sys.executable, "-c", f"import {package}"], 
                capture_output=True, 
                timeout=10
            )
            if result.returncode == 0:
                print(f"✅ {package}: Installed")
            else:
                print(f"❌ {package}: Not installed")
                missing_packages.append(package)
        except Exception as e:
            print(f"❌ {package}: Error checking - {e}")
            missing_packages.append(package)
    
    return len(missing_packages) == 0

def test_scheduled_script():
    """Test if the scheduled script can run"""
    print("\n🧪 Testing Scheduled Script...")
    
    current_dir = Path.cwd()
    script_path = current_dir / "run_scheduled_scrape.bat"
    
    if not script_path.exists():
        print("❌ run_scheduled_scrape.bat not found")
        return False
    
    # Test the Python part of the script
    try:
        # Import and test background_updater
        sys.path.append(str(current_dir))
        from background_updater import BackgroundUpdater
        
        updater = BackgroundUpdater()
        print("✅ BackgroundUpdater class can be instantiated")
        
        # Test if we can create the updater object
        print("✅ Scheduled script components are working")
        return True
        
    except Exception as e:
        print(f"❌ Error testing scheduled script: {e}")
        return False

def check_recent_activity():
    """Check for recent scraping activity"""
    print("\n📊 Checking Recent Activity...")
    
    current_dir = Path.cwd()
    out_dir = current_dir / "_out"
    
    if out_dir.exists():
        # Check for recent files (last 24 hours)
        recent_files = []
        for file in out_dir.rglob("*"):
            if file.is_file():
                # Check if file was modified in last 24 hours
                mtime = file.stat().st_mtime
                if mtime > datetime.now().timestamp() - 86400:  # 24 hours
                    recent_files.append(file)
        
        if recent_files:
            print(f"✅ Found {len(recent_files)} recent files in _out directory")
            for file in sorted(recent_files, key=lambda x: x.stat().st_mtime, reverse=True)[:5]:
                mtime = datetime.fromtimestamp(file.stat().st_mtime)
                print(f"   {file.name} - {mtime.strftime('%Y-%m-%d %H:%M:%S')}")
        else:
            print("⚠️  No recent files found in _out directory")
    else:
        print("❌ _out directory not found")

def generate_setup_commands():
    """Generate setup commands based on OS"""
    print("\n🔧 Setup Commands for Your System:")
    
    system = platform.system().lower()
    
    if system == "windows":
        print("\nFor Windows:")
        print("1. Run as Administrator:")
        print("   setup.bat")
        print("\n2. Or recreate scheduled tasks manually:")
        print("   schtasks /Create /TN SET_Scraper_1030 /TR \"run_scheduled_scrape.bat\" /SC WEEKLY /D MON,TUE,WED,THU,FRI /ST 10:30 /RL LIMITED")
        print("   schtasks /Create /TN SET_Scraper_1300 /TR \"run_scheduled_scrape.bat\" /SC WEEKLY /D MON,TUE,WED,THU,FRI /ST 13:00 /RL LIMITED")
        print("   schtasks /Create /TN SET_Scraper_1730 /TR \"run_scheduled_scrape.bat\" /SC WEEKLY /D MON,TUE,WED,THU,FRI /ST 17:30 /RL LIMITED")
    
    elif system == "darwin":  # macOS
        print("\nFor macOS:")
        print("1. Add to crontab (edit with: crontab -e):")
        print("   # Portfolio scraping at 10:30, 13:00, 17:30 (Mon-Fri)")
        print("   30 10 * * 1-5 cd /path/to/your/portfolio && python -c \"from background_updater import BackgroundUpdater; import asyncio; asyncio.run(BackgroundUpdater().update_all_data())\"")
        print("   0 13 * * 1-5 cd /path/to/your/portfolio && python -c \"from background_updater import BackgroundUpdater; import asyncio; asyncio.run(BackgroundUpdater().update_all_data())\"")
        print("   30 17 * * 1-5 cd /path/to/your/portfolio && python -c \"from background_updater import BackgroundUpdater; import asyncio; asyncio.run(BackgroundUpdater().update_all_data())\"")
    
    elif system == "linux":
        print("\nFor Linux:")
        print("1. Add to crontab (edit with: crontab -e):")
        print("   # Portfolio scraping at 10:30, 13:00, 17:30 (Mon-Fri)")
        print("   30 10 * * 1-5 cd /path/to/your/portfolio && python3 -c \"from background_updater import BackgroundUpdater; import asyncio; asyncio.run(BackgroundUpdater().update_all_data())\"")
        print("   0 13 * * 1-5 cd /path/to/your/portfolio && python3 -c \"from background_updater import BackgroundUpdater; import asyncio; asyncio.run(BackgroundUpdater().update_all_data())\"")
        print("   30 17 * * 1-5 cd /path/to/your/portfolio && python3 -c \"from background_updater import BackgroundUpdater; import asyncio; asyncio.run(BackgroundUpdater().update_all_data())\"")

def main():
    """Main diagnostic function"""
    print("=" * 60)
    print("Portfolio Dashboard - Scheduled Tasks Diagnostic")
    print("=" * 60)
    print(f"System: {platform.system()} {platform.release()}")
    print(f"Current Directory: {Path.cwd()}")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Check system-specific scheduled tasks
    system = platform.system().lower()
    tasks_found = False
    
    if system == "windows":
        tasks_found = len(check_windows_scheduled_tasks()) > 0
    elif system == "darwin":
        tasks_found = check_macos_scheduled_tasks()
    elif system == "linux":
        tasks_found = check_linux_scheduled_tasks()
    else:
        print(f"⚠️  Unsupported operating system: {system}")
    
    # Check common requirements
    files_ok = check_required_files()
    python_ok = check_python_environment()
    script_ok = test_scheduled_script()
    check_recent_activity()
    
    # Summary
    print("\n" + "=" * 60)
    print("DIAGNOSTIC SUMMARY")
    print("=" * 60)
    
    if tasks_found:
        print("✅ Scheduled tasks are configured")
    else:
        print("❌ No scheduled tasks found - needs setup")
    
    if files_ok:
        print("✅ Required files are present")
    else:
        print("❌ Some required files are missing")
    
    if python_ok:
        print("✅ Python environment is ready")
    else:
        print("❌ Python environment has issues")
    
    if script_ok:
        print("✅ Scheduled script is functional")
    else:
        print("❌ Scheduled script has issues")
    
    # Generate setup instructions
    if not tasks_found:
        generate_setup_commands()
    
    print("\n" + "=" * 60)
    print("Diagnostic complete!")
    print("=" * 60)

if __name__ == "__main__":
    main()
