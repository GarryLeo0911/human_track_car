#!/usr/bin/env python3
"""
Camera Test Script for Human Tracking Car
Tests all available camera options and provides recommendations
"""

import sys
import cv2
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def test_usb_cameras():
    """Test USB camera availability"""
    print("🔍 Testing USB Cameras...")
    working_cameras = []
    
    for i in range(5):  # Test first 5 camera indices
        try:
            cap = cv2.VideoCapture(i)
            if cap.isOpened():
                ret, frame = cap.read()
                if ret and frame is not None:
                    height, width = frame.shape[:2]
                    working_cameras.append({
                        'index': i,
                        'resolution': f"{width}x{height}",
                        'device': f"/dev/video{i}"
                    })
                    print(f"✅ USB Camera {i}: {width}x{height} - /dev/video{i}")
                cap.release()
            else:
                print(f"❌ Camera {i}: Not available")
        except Exception as e:
            print(f"❌ Camera {i}: Error - {e}")
    
    return working_cameras

def test_pi_camera_legacy():
    """Test original picamera library"""
    print("\n📷 Testing Pi Camera (Legacy)...")
    try:
        from picamera import PiCamera
        print("✅ picamera library available")
        
        try:
            camera = PiCamera()
            print("✅ Pi Camera hardware detected")
            camera.close()
            return True
        except Exception as e:
            print(f"❌ Pi Camera hardware error: {e}")
            return False
            
    except ImportError as e:
        print(f"❌ picamera library not available: {e}")
        return False

def test_pi_camera2():
    """Test picamera2 library"""
    print("\n📷 Testing Pi Camera (picamera2)...")
    try:
        # Test libcamera first
        try:
            import libcamera
            from libcamera import ControlType, Rectangle, Size
            print("✅ libcamera with ControlType available")
        except ImportError as e:
            print(f"❌ libcamera compatibility issue: {e}")
            return False
        
        # Test picamera2
        from picamera2 import Picamera2
        print("✅ picamera2 library available")
        
        try:
            camera = Picamera2()
            print("✅ Pi Camera hardware detected via picamera2")
            camera.close()
            return True
        except Exception as e:
            print(f"❌ Pi Camera hardware error: {e}")
            return False
            
    except ImportError as e:
        print(f"❌ picamera2 library error: {e}")
        return False

def test_opencv():
    """Test OpenCV"""
    print("\n🔧 Testing OpenCV...")
    try:
        import cv2
        print(f"✅ OpenCV version: {cv2.__version__}")
        return True
    except ImportError as e:
        print(f"❌ OpenCV not available: {e}")
        return False

def main():
    print("🚗 Human Tracking Car - Camera Test")
    print("=" * 50)
    
    # Test all camera options
    usb_cameras = test_usb_cameras()
    pi_legacy = test_pi_camera_legacy()
    pi_camera2 = test_pi_camera2()
    opencv_ok = test_opencv()
    
    print("\n" + "=" * 50)
    print("📋 SUMMARY")
    print("=" * 50)
    
    # USB Cameras
    if usb_cameras:
        print(f"✅ USB Cameras: {len(usb_cameras)} detected")
        for cam in usb_cameras:
            print(f"   - Camera {cam['index']}: {cam['resolution']}")
        print("   Recommendation: Use USB camera (most reliable)")
    else:
        print("❌ USB Cameras: None detected")
    
    # Pi Camera
    if pi_camera2:
        print("✅ Pi Camera (picamera2): Working")
        print("   Recommendation: Can use Pi Camera")
    elif pi_legacy:
        print("✅ Pi Camera (legacy): Working")
        print("   Recommendation: Can use Pi Camera (legacy mode)")
    else:
        print("❌ Pi Camera: Not working or not connected")
    
    # Overall recommendation
    print("\n🎯 RECOMMENDATION:")
    if usb_cameras:
        print("Use USB Camera - Most reliable for Ubuntu")
        print("Set in config/settings.py: USE_PI_CAMERA = False")
        print(f"Recommended camera: /dev/video{usb_cameras[0]['index']}")
    elif pi_camera2 or pi_legacy:
        print("Use Pi Camera - Working correctly")
        print("Set in config/settings.py: USE_PI_CAMERA = True")
    else:
        print("⚠️  No cameras detected!")
        print("1. Connect a USB camera, or")
        print("2. Check Pi Camera connection, or") 
        print("3. Run: sudo apt install libcamera-apps python3-picamera2")
    
    print("\n🚀 To run your tracking car:")
    print("1. Configure camera in config/settings.py")
    print("2. Activate virtual environment: source .venv/bin/activate")
    print("3. Run: python main.py")
    print("4. Open browser: http://your-pi-ip:5000")

if __name__ == "__main__":
    main()