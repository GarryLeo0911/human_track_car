# Ubuntu Setup Guide for Human Tracking Car

This guide provides Ubuntu-specific setup instructions for the Human Tracking Car project on Raspberry Pi 5.

## Prerequisites

### System Update
```bash
sudo apt update && sudo apt upgrade -y
```

### Install System Dependencies
```bash
# Essential build tools
sudo apt install -y build-essential cmake pkg-config

# Python development tools
sudo apt install -y python3-dev python3-pip python3-venv

# OpenCV dependencies
sudo apt install -y libjpeg-dev libtiff5-dev libpng-dev
sudo apt install -y libavcodec-dev libavformat-dev libswscale-dev libv4l-dev
sudo apt install -y libxvidcore-dev libx264-dev
sudo apt install -y libfontconfig1-dev libcairo2-dev
sudo apt install -y libgdk-pixbuf2.0-dev libpango1.0-dev
sudo apt install -y libgtk2.0-dev libgtk-3-dev
sudo apt install -y libatlas-base-dev gfortran
sudo apt install -y libhdf5-dev libhdf5-serial-dev libhdf5-103

# I2C tools and GPIO access
sudo apt install -y i2c-tools python3-smbus
sudo apt install -y gpio python3-gpiozero

# Camera support
sudo apt install -y v4l-utils
```

### Enable Hardware Interfaces

#### Enable I2C
```bash
# Add to /boot/firmware/config.txt
echo "dtparam=i2c_arm=on" | sudo tee -a /boot/firmware/config.txt

# Load I2C modules
echo "i2c-dev" | sudo tee -a /etc/modules
```

#### Enable Camera
```bash
# For USB cameras (automatic)
# For Raspberry Pi Camera Module, add to /boot/firmware/config.txt:
echo "start_x=1" | sudo tee -a /boot/firmware/config.txt
echo "gpu_mem=128" | sudo tee -a /boot/firmware/config.txt
```

#### Set GPU Memory Split
```bash
# Add to /boot/firmware/config.txt for better camera performance
echo "gpu_mem=128" | sudo tee -a /boot/firmware/config.txt
```

### User Permissions
```bash
# Add user to gpio and i2c groups
sudo usermod -a -G gpio,i2c,video $USER

# Reboot to apply changes
sudo reboot
```

## Project Setup

### 1. Clone and Setup Virtual Environment
```bash
git clone <your-repo-url>
cd human_track_car

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install Ubuntu-compatible requirements
pip install -r requirements-ubuntu.txt
```

### 2. Test Hardware

#### Test I2C Communication
```bash
# Scan for I2C devices
sudo i2cdetect -y 1

# Should show PCA9685 at address 0x40 (default)
```

#### Test Camera
```bash
# For USB camera
v4l2-ctl --list-devices

# For Pi Camera with picamera2
python3 -c "from picamera2 import Picamera2; print('Camera OK')"
```

#### Test GPIO Access
```bash
# Test with gpiozero
python3 -c "from gpiozero import LED; print('GPIO OK')"
```

## Configuration Adjustments

### Camera Configuration
For Ubuntu, you may need to adjust camera settings in `config/settings.py`:

```python
# Ubuntu-specific camera settings
USE_PI_CAMERA = True  # Works with picamera2
CAMERA_RESOLUTION = (640, 480)
CAMERA_FRAMERATE = 30

# V4L2 settings for USB cameras
USB_CAMERA_DEVICE = '/dev/video0'
```

### GPIO Library Configuration
The motor controller automatically detects and uses the best available GPIO library, but you can force specific modes if needed.

## Troubleshooting

### Camera Issues
```bash
# Check camera permissions
ls -la /dev/video*

# Test with v4l2
v4l2-ctl --device=/dev/video0 --list-formats

# For Pi Camera
libcamera-hello --list-cameras
```

### I2C Issues
```bash
# Check I2C bus
sudo i2cdetect -y 1

# Check permissions
groups $USER
```

### GPIO Issues
```bash
# Test GPIO access
python3 -c "import gpiozero; print('GPIO access OK')"

# Check user groups
id
```

## Performance Optimization

### System Optimization
```bash
# Increase GPU memory for better camera performance
sudo raspi-config
# Advanced Options > Memory Split > 128

# Disable unnecessary services
sudo systemctl disable bluetooth
sudo systemctl disable wifi-powersave
```

### Python Optimization
```bash
# Install optimized NumPy
pip install numpy --upgrade

# Use compiled OpenCV
pip install opencv-python --upgrade
```

## Running the Application

```bash
# Activate environment
source .venv/bin/activate

# Run with Ubuntu optimizations
python main.py
```

## Ubuntu vs Raspberry Pi OS Differences

| Feature | Raspberry Pi OS | Ubuntu |
|---------|----------------|---------|
| GPIO Library | RPi.GPIO | gpiozero (recommended) |
| Camera Library | picamera | picamera2 |
| I2C Tools | Built-in | Requires i2c-tools |
| Boot Config | /boot/config.txt | /boot/firmware/config.txt |
| Package Manager | apt | apt |
| Python Default | 3.9+ | 3.10+ |

## Additional Notes

- Ubuntu on Pi 5 uses different boot configuration paths
- Some timing-sensitive operations may behave differently
- GPIO access requires proper user permissions
- Camera module support requires specific kernel modules
- I2C communication should work identically to Raspberry Pi OS