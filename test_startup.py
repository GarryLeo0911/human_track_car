"""
Test script to verify the fixes work
"""

import sys
import time
import requests
import threading

def test_app_startup():
    """Test if the app starts without hanging."""
    print("Testing app startup...")
    
    # Import and start the app in a thread
    def start_app():
        try:
            from main import main
            main()
        except Exception as e:
            print(f"Error in app: {e}")
    
    app_thread = threading.Thread(target=start_app, daemon=True)
    app_thread.start()
    
    # Wait a bit for startup
    print("Waiting for app to start...")
    time.sleep(5)
    
    # Test if we can reach the app
    try:
        response = requests.get('http://127.0.0.1:5000', timeout=5)
        if response.status_code == 200:
            print("✅ App is responding!")
            return True
        else:
            print(f"❌ App responded with status {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Could not reach app: {e}")
        return False

def test_endpoints():
    """Test various endpoints."""
    print("\nTesting API endpoints...")
    
    endpoints = [
        '/api/status',
        '/api/settings'
    ]
    
    for endpoint in endpoints:
        try:
            response = requests.get(f'http://127.0.0.1:5000{endpoint}', timeout=5)
            if response.status_code == 200:
                print(f"✅ {endpoint} - OK")
            else:
                print(f"❌ {endpoint} - Status {response.status_code}")
        except requests.exceptions.RequestException as e:
            print(f"❌ {endpoint} - Error: {e}")

def main():
    """Main test function."""
    print("Human Tracking Car - Startup Test")
    print("=" * 40)
    
    # Test startup
    if test_app_startup():
        test_endpoints()
        print("\n✅ Basic tests passed! The app should be working now.")
        print("Try accessing http://127.0.0.1:5000 in your browser.")
    else:
        print("\n❌ App startup failed.")
    
    print("\nPress Ctrl+C to exit...")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nExiting...")

if __name__ == "__main__":
    main()