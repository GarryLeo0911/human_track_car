#!/bin/bash
# Ubuntu Setup Script for Human Tracking Car on Raspberry Pi 5

set -e

echo "🚗 Human Tracking Car - Ubuntu Setup Script"
echo "==========================================="

# Check if running on Ubuntu
if [[ ! -f /etc/os-release ]] || ! grep -q "Ubuntu" /etc/os-release; then
    echo "⚠️  This script is designed for Ubuntu. Continue anyway? (y/N)"
    read -r response
    if [[ ! "$response" =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Update system
echo "📦 Updating system packages..."
sudo apt update && sudo apt upgrade -y

# Install system dependencies
echo "🔧 Installing system dependencies..."
sudo apt install -y \
    build-essential cmake pkg-config \
    python3-dev python3-pip python3-venv \
    libjpeg-dev libtiff5-dev libpng-dev \
    libavcodec-dev libavformat-dev libswscale-dev libv4l-dev \
    libxvidcore-dev libx264-dev \
    libfontconfig1-dev libcairo2-dev \
    libgdk-pixbuf2.0-dev libpango1.0-dev \
    libgtk2.0-dev libgtk-3-dev \
    libatlas-base-dev gfortran \
    libhdf5-dev libhdf5-serial-dev libhdf5-103 \
    i2c-tools python3-smbus \
    gpio python3-gpiozero \
    v4l-utils \
    git

# Install libcamera and camera-specific dependencies
echo "📷 Installing camera system dependencies..."
sudo apt install -y \
    libcamera-dev \
    libcamera-apps \
    python3-libcamera \
    python3-kms++ \
    python3-pyqt5 \
    python3-prctl \
    libatlas-base-dev \
    ffmpeg \
    python3-numpy

# Enable hardware interfaces
echo "⚙️  Configuring hardware interfaces..."

# Enable I2C
if ! grep -q "dtparam=i2c_arm=on" /boot/firmware/config.txt; then
    echo "dtparam=i2c_arm=on" | sudo tee -a /boot/firmware/config.txt
    echo "✅ I2C enabled"
fi

# Enable camera
echo "📷 Configuring camera support..."
# For Ubuntu, we need different camera configuration
if ! grep -q "dtoverlay=vc4-kms-v3d" /boot/firmware/config.txt; then
    echo "dtoverlay=vc4-kms-v3d" | sudo tee -a /boot/firmware/config.txt
    echo "✅ GPU driver enabled"
fi

if ! grep -q "camera_auto_detect=1" /boot/firmware/config.txt; then
    echo "camera_auto_detect=1" | sudo tee -a /boot/firmware/config.txt
    echo "✅ Camera auto-detect enabled"
fi

# GPU memory is less critical on Ubuntu but still helpful
if ! grep -q "gpu_mem=128" /boot/firmware/config.txt; then
    echo "gpu_mem=128" | sudo tee -a /boot/firmware/config.txt
    echo "✅ GPU memory configured"
fi

# Load I2C module
if ! grep -q "i2c-dev" /etc/modules; then
    echo "i2c-dev" | sudo tee -a /etc/modules
    echo "✅ I2C module configured"
fi

# Add user to required groups
echo "👤 Adding user to hardware groups..."
sudo usermod -a -G gpio,i2c,video $USER

# Create virtual environment
echo "🐍 Setting up Python virtual environment..."
if [ ! -d ".venv" ]; then
    python3 -m venv .venv
    echo "✅ Virtual environment created"
fi

# Activate virtual environment and install packages
echo "📚 Installing Python packages..."
source .venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install Ubuntu-compatible requirements
if [ -f "requirements-ubuntu.txt" ]; then
    pip install -r requirements-ubuntu.txt
    echo "✅ Ubuntu requirements installed"
elif [ -f "requirements.txt" ]; then
    echo "⚠️  Using standard requirements.txt. Consider creating requirements-ubuntu.txt"
    pip install -r requirements.txt
else
    echo "⚠️  No requirements file found. Installing basic packages..."
    pip install flask opencv-python numpy gpiozero adafruit-circuitpython-pca9685
fi

# Install picamera2 via system package (recommended for Ubuntu)
echo "📷 Installing picamera2 via system package..."
sudo apt install -y python3-picamera2

# Make sure the virtual environment can access system packages
echo "🔗 Configuring virtual environment for system packages..."
# Add system packages to virtual environment
SITE_PACKAGES=$(python -c "import site; print(site.getsitepackages()[0])")
SYSTEM_PACKAGES="/usr/lib/python3/dist-packages"
if [ ! -f "$SITE_PACKAGES/system_packages.pth" ]; then
    echo "$SYSTEM_PACKAGES" > "$SITE_PACKAGES/system_packages.pth"
    echo "✅ System packages linked to virtual environment"
fi

# Test hardware
echo "🔍 Testing hardware..."

# Test I2C
if command -v i2cdetect >/dev/null 2>&1; then
    echo "I2C devices:"
    sudo i2cdetect -y 1 || echo "⚠️  No I2C devices found"
else
    echo "⚠️  i2cdetect not available"
fi

# Test camera
echo "Testing camera access..."
if ls /dev/video* >/dev/null 2>&1; then
    echo "✅ Camera devices found: $(ls /dev/video*)"
else
    echo "⚠️  No camera devices found"
fi

# Test GPIO
python3 -c "
try:
    import gpiozero
    print('✅ GPIO access OK')
except Exception as e:
    print(f'⚠️  GPIO error: {e}')
" 2>/dev/null || echo "⚠️  GPIO test failed"

# Test camera libraries
echo "Testing Python camera libraries..."
python3 -c "
import sys
import os

# Test libcamera availability
try:
    import libcamera
    print('✅ libcamera available')
except ImportError as e:
    print(f'⚠️  libcamera not available: {e}')

# Test picamera2 availability
try:
    from picamera2 import Picamera2
    print('✅ picamera2 available')
    
    # Try to create a camera instance (don't start it)
    try:
        cam = Picamera2()
        print('✅ picamera2 can create camera instance')
        cam.close()
    except Exception as e:
        print(f'⚠️  picamera2 camera creation failed: {e}')
        
except ImportError as e:
    print(f'⚠️  picamera2 not available: {e}')
    print('   Try: sudo apt install python3-picamera2')

# Test OpenCV
try:
    import cv2
    print('✅ OpenCV available')
except ImportError as e:
    print(f'⚠️  OpenCV not available: {e}')

# Test if we can detect any cameras
try:
    import cv2
    for i in range(3):
        cap = cv2.VideoCapture(i)
        if cap.isOpened():
            print(f'✅ USB Camera {i} detected')
            cap.release()
            break
    else:
        print('⚠️  No USB cameras detected')
except Exception as e:
    print(f'⚠️  Camera detection failed: {e}')
" 2>/dev/null || echo "⚠️  Camera library test failed"

# Test libcamera command line tools
echo "Testing libcamera command line tools..."
if command -v libcamera-hello >/dev/null 2>&1; then
    echo "✅ libcamera-hello available"
    # Quick camera test (timeout after 1 second)
    timeout 1s libcamera-hello --list-cameras 2>/dev/null || echo "⚠️  No cameras detected by libcamera"
else
    echo "⚠️  libcamera-hello not available"
fi

echo ""
echo "🎉 Setup complete!"
echo ""
echo "Next steps:"
echo "1. Reboot your Raspberry Pi: sudo reboot"
echo "2. After reboot, activate the virtual environment: source .venv/bin/activate"
echo "3. Run the application: python main.py"
echo "4. Open web interface at: http://$(hostname -I | awk '{print $1}'):5000"
echo ""
echo "If you need to install additional packages:"
echo "  source .venv/bin/activate"
echo "  pip install package_name"
echo ""
echo "For troubleshooting, check UBUNTU_SETUP.md"

# Check if reboot is needed
if [ -f /var/run/reboot-required ]; then
    echo ""
    echo "⚠️  System reboot required for hardware changes to take effect"
    echo "   Run: sudo reboot"
fi