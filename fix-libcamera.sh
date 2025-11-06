#!/bin/bash
# Quick fix for libcamera module issue on Ubuntu

echo "🔧 Quick Fix for 'no module named libcamera'"
echo "============================================"

echo "📦 Installing libcamera system packages..."
sudo apt update
sudo apt install -y \
    libcamera-dev \
    libcamera-apps \
    python3-libcamera \
    python3-picamera2 \
    python3-kms++ \
    python3-pyqt5 \
    python3-prctl

echo "🔗 Setting up virtual environment to access system packages..."

# If you're in a virtual environment, link system packages
if [[ "$VIRTUAL_ENV" != "" ]]; then
    echo "Virtual environment detected: $VIRTUAL_ENV"
    
    # Create path file to include system packages
    SITE_PACKAGES=$(python -c "import site; print(site.getsitepackages()[0])")
    SYSTEM_PACKAGES="/usr/lib/python3/dist-packages"
    
    echo "Creating system package link..."
    echo "$SYSTEM_PACKAGES" > "$SITE_PACKAGES/system_packages.pth"
    echo "✅ System packages linked"
else
    echo "⚠️  No virtual environment detected. You may need to activate it first:"
    echo "   source .venv/bin/activate"
fi

echo ""
echo "🧪 Testing the fix..."

python3 -c "
try:
    import libcamera
    print('✅ SUCCESS: libcamera module now available!')
except ImportError as e:
    print(f'❌ FAILED: libcamera still not available: {e}')
    print('')
    print('Additional steps needed:')
    print('1. Make sure you\\'re in the virtual environment: source .venv/bin/activate')
    print('2. Reboot your Pi: sudo reboot')
    print('3. Run the troubleshoot script: ./troubleshoot-libcamera.sh')

try:
    from picamera2 import Picamera2
    print('✅ SUCCESS: picamera2 module available!')
except ImportError as e:
    print(f'❌ FAILED: picamera2 not available: {e}')
"

echo ""
echo "📋 Next Steps:"
echo "1. If tests passed: You're ready to run your tracking car!"
echo "2. If tests failed: Run the troubleshoot script:"
echo "   chmod +x troubleshoot-libcamera.sh"
echo "   ./troubleshoot-libcamera.sh"
echo ""
echo "3. You may need to reboot: sudo reboot"
echo ""
echo "4. To run your project:"
echo "   source .venv/bin/activate"
echo "   python main.py"