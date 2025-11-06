#!/bin/bash
# Libcamera Troubleshooting Script for Ubuntu on Raspberry Pi 5

echo "🔧 Libcamera Troubleshooting for Ubuntu"
echo "======================================"

# Check Ubuntu version
echo "📋 System Information:"
lsb_release -a 2>/dev/null || echo "LSB not available"
uname -a

echo ""
echo "📦 Checking libcamera packages:"

# Check if libcamera packages are installed
packages=(
    "libcamera-dev"
    "libcamera-apps" 
    "python3-libcamera"
    "python3-picamera2"
)

for package in "${packages[@]}"; do
    if dpkg -l | grep -q "$package"; then
        version=$(dpkg -l | grep "$package" | awk '{print $3}')
        echo "✅ $package: $version"
    else
        echo "❌ $package: NOT INSTALLED"
    fi
done

echo ""
echo "🔍 Camera Detection:"

# Check for camera devices
echo "Camera devices:"
ls -la /dev/video* 2>/dev/null || echo "No /dev/video* devices found"

echo ""
echo "Camera base device:"
ls -la /base/soc/i2c* 2>/dev/null || echo "No i2c camera devices found"

echo ""
echo "🧪 Testing libcamera:"

# Test libcamera command line
if command -v libcamera-hello >/dev/null 2>&1; then
    echo "libcamera-hello found, listing cameras:"
    timeout 3s libcamera-hello --list-cameras 2>&1 || echo "Camera listing timed out or failed"
else
    echo "libcamera-hello not found"
fi

echo ""
echo "🐍 Testing Python imports:"

# Test Python imports
python3 -c "
import sys
print(f'Python version: {sys.version}')
print(f'Python path: {sys.path}')

print('\nTesting imports:')

try:
    import libcamera
    print('✅ libcamera module imported successfully')
    print(f'   libcamera version: {getattr(libcamera, \"__version__\", \"unknown\")}')
except ImportError as e:
    print(f'❌ libcamera import failed: {e}')
    print('   This is the main issue!')

try:
    from picamera2 import Picamera2
    print('✅ picamera2 imported successfully')
except ImportError as e:
    print(f'❌ picamera2 import failed: {e}')

try:
    import cv2
    print(f'✅ OpenCV version: {cv2.__version__}')
except ImportError as e:
    print(f'❌ OpenCV import failed: {e}')
"

echo ""
echo "🔧 Potential Solutions:"

echo ""
echo "1. Install missing packages:"
echo "   sudo apt update"
echo "   sudo apt install -y libcamera-dev libcamera-apps python3-libcamera python3-picamera2"

echo ""
echo "2. If still failing, try installing from source:"
echo "   # This is more complex and takes time"
echo "   sudo apt install -y meson ninja-build"
echo "   git clone https://git.libcamera.org/libcamera/libcamera.git"
echo "   cd libcamera"
echo "   meson build"
echo "   ninja -C build install"

echo ""
echo "3. Alternative - Use USB camera only:"
echo "   # Modify your code to skip Pi camera and use USB camera"
echo "   # Set USE_PI_CAMERA = False in config/settings.py"

echo ""
echo "4. Check boot configuration:"
echo "   # Make sure /boot/firmware/config.txt has:"
echo "   dtoverlay=vc4-kms-v3d"
echo "   camera_auto_detect=1"

echo ""
echo "5. Reboot after making changes:"
echo "   sudo reboot"

echo ""
echo "📞 Getting Help:"
echo "If the issue persists:"
echo "1. Check Ubuntu version compatibility with libcamera"
echo "2. Verify Raspberry Pi 5 camera module connection"
echo "3. Try with a fresh Ubuntu installation"
echo "4. Consider using Raspberry Pi OS if camera is critical"

echo ""
echo "🔍 Current boot config:"
if [ -f "/boot/firmware/config.txt" ]; then
    echo "Camera-related settings in /boot/firmware/config.txt:"
    grep -E "(camera|dtoverlay|gpu_mem)" /boot/firmware/config.txt || echo "No camera settings found"
else
    echo "/boot/firmware/config.txt not found"
fi