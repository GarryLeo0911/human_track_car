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

# Enable hardware interfaces
echo "⚙️  Configuring hardware interfaces..."

# Enable I2C
if ! grep -q "dtparam=i2c_arm=on" /boot/firmware/config.txt; then
    echo "dtparam=i2c_arm=on" | sudo tee -a /boot/firmware/config.txt
    echo "✅ I2C enabled"
fi

# Enable camera
if ! grep -q "start_x=1" /boot/firmware/config.txt; then
    echo "start_x=1" | sudo tee -a /boot/firmware/config.txt
    echo "gpu_mem=128" | sudo tee -a /boot/firmware/config.txt
    echo "✅ Camera enabled"
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
    pip install flask opencv-python numpy gpiozero picamera2 adafruit-circuitpython-pca9685
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
python3 -c "
try:
    from picamera2 import Picamera2
    print('✅ picamera2 available')
except ImportError:
    print('⚠️  picamera2 not available')

try:
    import cv2
    print('✅ OpenCV available')
except ImportError:
    print('⚠️  OpenCV not available')
" 2>/dev/null || echo "⚠️  Camera library test failed"

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