#!/bin/bash

# Human Tracking Car - Raspberry Pi Installation Script
# This script installs all required dependencies for the human tracking car on Raspberry Pi OS

echo "===================="
echo "Human Tracking Car - Raspberry Pi Setup"
echo "===================="

# Update system packages
echo "Updating system packages..."
sudo apt update && sudo apt upgrade -y

# Install system dependencies
echo "Installing system dependencies..."
sudo apt install -y \
    python3-pip \
    python3-dev \
    python3-setuptools \
    python3-venv \
    build-essential \
    cmake \
    pkg-config \
    libjpeg-dev \
    libtiff5-dev \
    libjasper-dev \
    libpng-dev \
    libavcodec-dev \
    libavformat-dev \
    libswscale-dev \
    libv4l-dev \
    libxvidcore-dev \
    libx264-dev \
    libgtk-3-dev \
    libcanberra-gtk-module \
    libcanberra-gtk3-module \
    libatlas-base-dev \
    gfortran \
    python3-numpy

# Install Raspberry Pi specific packages
echo "Installing Raspberry Pi specific packages..."
sudo apt install -y \
    python3-picamera2 \
    python3-libcamera \
    python3-kms++ \
    libcamera-apps

# Install GPIO libraries
echo "Installing GPIO libraries..."
sudo apt install -y \
    python3-rpi.gpio \
    python3-gpiozero

# Create virtual environment (optional but recommended)
echo "Creating virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip

# Install OpenCV for Raspberry Pi
echo "Installing OpenCV..."
# For Raspberry Pi, it's often better to use the system package
sudo apt install -y python3-opencv

# Alternative: Install via pip (may take a very long time to compile)
# pip install opencv-python

# Install other Python packages
echo "Installing Python packages..."
pip install flask
pip install numpy
pip install imutils
pip install adafruit-circuitpython-pca9685
pip install adafruit-circuitpython-motor
pip install adafruit-blinka
pip install pygame

# Enable camera interface
echo "Enabling camera interface..."
sudo raspi-config nonint do_camera 0

# Enable I2C interface
echo "Enabling I2C interface..."
sudo raspi-config nonint do_i2c 0

# Enable SPI interface
echo "Enabling SPI interface..."
sudo raspi-config nonint do_spi 0

echo "===================="
echo "Installation completed!"
echo "===================="
echo "Please reboot your Raspberry Pi to ensure all changes take effect:"
echo "sudo reboot"
echo ""
echo "After reboot, test the installation by running:"
echo "python3 -c 'import cv2; print(\"OpenCV version:\", cv2.__version__)'"
echo ""
echo "To run the human tracking car:"
echo "cd /path/to/human_track_car"
echo "source venv/bin/activate  # if using virtual environment"
echo "python3 main.py"