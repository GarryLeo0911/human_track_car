#!/bin/bash
# Fix for libcamera ControlType import error on Ubuntu

echo "🔧 Fixing libcamera ControlType Import Error"
echo "==========================================="

echo "📋 Current situation:"
echo "- picamera2 is installed ✅"
echo "- libcamera is available but has version compatibility issues ⚠️"
echo "- Error: cannot import name 'ControlType' from 'libcamera'"

echo ""
echo "📦 Step 1: Remove pip-installed picamera2 and use system package"

# Remove pip version
pip uninstall -y picamera2

echo "✅ Removed pip-installed picamera2"

echo ""
echo "📦 Step 2: Install system packages for libcamera"

sudo apt update
sudo apt install -y \
    libcamera-dev \
    libcamera-apps \
    libcamera-tools \
    python3-libcamera \
    python3-picamera2

echo "✅ Installed system libcamera packages"

echo ""
echo "🔗 Step 3: Link system packages to virtual environment"

# Get virtual environment site-packages path
SITE_PACKAGES=$(python -c "import site; print(site.getsitepackages()[0])" 2>/dev/null)
SYSTEM_PACKAGES="/usr/lib/python3/dist-packages"

if [[ "$VIRTUAL_ENV" != "" && -n "$SITE_PACKAGES" ]]; then
    echo "Virtual environment detected: $VIRTUAL_ENV"
    echo "Site packages: $SITE_PACKAGES"
    
    # Create system packages path file
    echo "$SYSTEM_PACKAGES" > "$SITE_PACKAGES/system_packages.pth"
    echo "✅ System packages linked to virtual environment"
else
    echo "⚠️  No virtual environment detected or site-packages not found"
    echo "You may need to:"
    echo "1. Activate virtual environment: source .venv/bin/activate"
    echo "2. Re-run this script"
fi

echo ""
echo "🧪 Step 4: Test the fix"

python3 -c "
import sys
print(f'Python path includes:')
for p in sys.path[:5]:  # Show first 5 paths
    print(f'  {p}')
print('  ...')

print('\nTesting imports:')

# Test libcamera
try:
    import libcamera
    print('✅ libcamera imported successfully')
    
    # Test specific imports that were failing
    try:
        from libcamera import ControlType, Rectangle, Size
        print('✅ ControlType, Rectangle, Size imported successfully')
    except ImportError as e:
        print(f'❌ Still cannot import ControlType: {e}')
        print('   This suggests libcamera version is still incompatible')
        
except ImportError as e:
    print(f'❌ libcamera import failed: {e}')

# Test picamera2
try:
    from picamera2 import Picamera2
    print('✅ picamera2 imported successfully')
    
    # Try to create instance (don't start)
    try:
        cam = Picamera2()
        print('✅ picamera2 camera instance created')
        cam.close()
    except Exception as e:
        print(f'⚠️  picamera2 camera creation failed: {e}')
        print('   This is normal if no camera is connected')
        
except ImportError as e:
    print(f'❌ picamera2 import failed: {e}')
"

echo ""
echo "📋 Results and Next Steps:"

# Check if the fix worked
if python3 -c "from libcamera import ControlType; from picamera2 import Picamera2" 2>/dev/null; then
    echo "🎉 SUCCESS! libcamera compatibility issue resolved!"
    echo ""
    echo "✅ You can now run your tracking car:"
    echo "   source .venv/bin/activate  # if not already activated"
    echo "   python main.py"
else
    echo "⚠️  The issue persists. Additional options:"
    echo ""
    echo "Option 1: Use USB camera instead"
    echo "  - Edit config/settings.py"
    echo "  - Set USE_PI_CAMERA = False"
    echo "  - This bypasses Pi Camera entirely"
    echo ""
    echo "Option 2: Check Ubuntu version compatibility"
    echo "  - Run: lsb_release -a"
    echo "  - Some Ubuntu versions have libcamera compatibility issues"
    echo ""
    echo "Option 3: Build libcamera from source (advanced)"
    echo "  - This takes 30+ minutes but ensures compatibility"
    echo "  - Let me know if you want instructions for this"
fi

echo ""
echo "🔍 Camera devices detected:"
ls -la /dev/video* 2>/dev/null || echo "No video devices found"

echo ""
echo "📷 You have these camera options working:"
if ls /dev/video* >/dev/null 2>&1; then
    echo "✅ USB cameras available"
else
    echo "❌ No USB cameras detected"
fi

if python3 -c "from picamera2 import Picamera2" 2>/dev/null; then
    echo "✅ Pi Camera (picamera2) available"
else
    echo "❌ Pi Camera not working"
fi