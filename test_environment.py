#!/usr/bin/env python3
"""
Test script to verify OpenCV installation and basic functionality
Run this script to check if your environment is properly set up
"""

import sys
import os

def test_opencv():
    """Test OpenCV installation and basic functionality"""
    print("=" * 50)
    print("Testing OpenCV Installation")
    print("=" * 50)
    
    try:
        import cv2
        print(f"✓ OpenCV imported successfully")
        print(f"✓ OpenCV version: {cv2.__version__}")
    except ImportError as e:
        print(f"✗ Failed to import OpenCV: {e}")
        print("\nTo fix this on Raspberry Pi OS:")
        print("1. sudo apt install python3-opencv")
        print("2. Or run: pip install opencv-python")
        return False
    
    # Test basic OpenCV functionality
    try:
        # Test image creation
        import numpy as np
        img = np.zeros((100, 100, 3), dtype=np.uint8)
        img = cv2.rectangle(img, (10, 10), (90, 90), (255, 255, 255), 2)
        print("✓ Basic OpenCV operations work")
    except Exception as e:
        print(f"✗ OpenCV basic operations failed: {e}")
        return False
    
    return True

def test_camera():
    """Test camera availability"""
    print("\n" + "=" * 50)
    print("Testing Camera Availability")
    print("=" * 50)
    
    # Check for Pi Camera
    try:
        from picamera2 import Picamera2
        print("✓ picamera2 library available")
        
        # Try to initialize camera
        try:
            picam2 = Picamera2()
            print("✓ Pi Camera detected and accessible")
            picam2.close()
        except Exception as e:
            print(f"⚠ Pi Camera not accessible: {e}")
    except ImportError:
        print("⚠ picamera2 not installed (install with: sudo apt install python3-picamera2)")
    
    # Check for USB cameras
    import cv2
    for i in range(3):  # Check first 3 video devices
        cap = cv2.VideoCapture(i)
        if cap.isOpened():
            print(f"✓ USB Camera found at /dev/video{i}")
            cap.release()
            break
    else:
        print("⚠ No USB cameras detected")

def test_gpio():
    """Test GPIO availability"""
    print("\n" + "=" * 50)
    print("Testing GPIO Libraries")
    print("=" * 50)
    
    try:
        import RPi.GPIO as GPIO
        print("✓ RPi.GPIO imported successfully")
    except ImportError:
        print("⚠ RPi.GPIO not available (install with: sudo apt install python3-rpi.gpio)")
    
    try:
        import gpiozero
        print("✓ gpiozero imported successfully")
    except ImportError:
        print("⚠ gpiozero not available (install with: pip install gpiozero)")

def test_other_dependencies():
    """Test other required dependencies"""
    print("\n" + "=" * 50)
    print("Testing Other Dependencies")
    print("=" * 50)
    
    dependencies = [
        ('numpy', 'NumPy'),
        ('flask', 'Flask'),
        ('imutils', 'imutils'),
    ]
    
    for module, name in dependencies:
        try:
            __import__(module)
            print(f"✓ {name} imported successfully")
        except ImportError:
            print(f"✗ {name} not available (install with: pip install {module})")

def main():
    """Run all tests"""
    print("Human Tracking Car - Environment Test")
    print(f"Python version: {sys.version}")
    print(f"Platform: {sys.platform}")
    
    # Run tests
    opencv_ok = test_opencv()
    test_camera()
    test_gpio()
    test_other_dependencies()
    
    print("\n" + "=" * 50)
    print("Test Summary")
    print("=" * 50)
    
    if opencv_ok:
        print("✓ Environment appears to be ready!")
        print("You can now run: python3 main.py")
    else:
        print("✗ Please fix the OpenCV installation first")
        print("Run the installation script: ./install_raspberry_pi.sh")

if __name__ == "__main__":
    main()