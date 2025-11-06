# Human Tracking Car

An automatic human tracking car based on the Freenove 4WD Smart Car Kit for Raspberry Pi. This project uses computer vision to detect and follow humans while keeping them centered in the camera frame.

![Python](https://img.shields.io/badge/Python-3.8+-blue)
![OpenCV](https://img.shields.io/badge/OpenCV-4.0+-green)
![Flask](https://img.shields.io/badge/Flask-2.0+-red)
![Raspberry Pi](https://img.shields.io/badge/Raspberry%20Pi-4-red)

## Features

- **Real-time Human Detection**: Uses OpenCV HOG descriptor for robust human detection
- **Automatic Tracking**: PID-controlled movement to keep humans centered in frame
- **Web Interface**: Real-time video streaming with control dashboard
- **Manual Control**: Remote control capabilities via web interface or keyboard
- **Modular Design**: Separated concerns for easy maintenance and upgrades
- **Dual Camera Support**: Works with both Pi Camera and USB cameras
- **Safety Features**: Automatic stopping when no human is detected

## Hardware Requirements

### Required Components
- Freenove 4WD Smart Car Kit for Raspberry Pi (FNK0043)
- Raspberry Pi 4 (recommended) or Raspberry Pi 3B+
- Pi Camera Module or USB Webcam
- MicroSD Card (32GB+ recommended)
- Power bank or battery pack

### Optional Components
- Pan-tilt servo mount for camera (for advanced tracking)
- LED lights for better low-light detection
- Ultrasonic sensor for distance measurement

## Software Requirements

- Python 3.8+
- OpenCV 4.0+
- Flask 2.0+
- NumPy
- Additional packages listed in `requirements.txt`

## Installation

### 1. Setup Raspberry Pi

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python dependencies
sudo apt install python3-pip python3-venv git

# Enable camera interface
sudo raspi-config
# Navigate to Interface Options > Camera > Enable
```

### 2. Clone and Setup Project

```bash
# Clone the repository
git clone <repository-url>
cd human_track

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install Python packages
pip install -r requirements.txt
```

### 3. Hardware Setup

1. **Assemble the Freenove 4WD Smart Car** following the official guide
2. **Connect the Pi Camera** or USB webcam
3. **Verify motor connections** match the pin configuration in `src/control/motor_controller.py`
4. **Test camera functionality**:
   ```bash
   # For Pi Camera
   raspistill -v -o test.jpg
   
   # For USB Camera
   ls /dev/video*
   ```

### 4. Configuration

Edit `config/settings.py` to match your hardware setup:

```python
# Camera settings
USE_PI_CAMERA = True  # Set to False for USB camera
CAMERA_RESOLUTION = (640, 480)

# Motor settings - adjust pin numbers if needed
# Check motor_controller.py for pin configurations

# PID tuning - adjust for your car's responsiveness
PID_X_KP = 0.5  # Increase for faster turning response
PID_DISTANCE_KP = 0.3  # Increase for faster approach/retreat
```

## Usage

### Starting the Application

```bash
# Activate virtual environment
source .venv/bin/activate

# Run the application
python main.py
```

The web interface will be available at: `http://[raspberry-pi-ip]:5000`

### Web Interface Controls

- **Start/Stop Tracking**: Begin or end automatic human following
- **Manual Control**: Use directional buttons or keyboard (WASD/Arrow keys)
- **Speed Control**: Adjust movement speed (0-100%)
- **Settings**: Tune PID parameters and detection settings
- **Status Monitoring**: View real-time system status and detection info

### Keyboard Controls (when web interface is focused)

- `W` / `↑`: Move forward
- `S` / `↓`: Move backward  
- `A` / `←`: Turn left
- `D` / `→`: Turn right
- `Space`: Stop
- Manual controls are disabled during automatic tracking

## How It Works

### 1. Human Detection
The system uses OpenCV's HOG (Histogram of Oriented Gradients) descriptor with SVM classification to detect humans in real-time:

```python
# Detection pipeline
frame → resize → HOG detection → confidence filtering → bounding box
```

### 2. Tracking Algorithm
A PID controller system manages car movement:

- **X-axis PID**: Controls turning to keep human centered
- **Distance PID**: Controls forward/backward movement based on human size
- **Deadzone filtering**: Prevents jittery movements

### 3. Motor Control
The 4WD system uses differential steering:
- Independent control of left and right motor pairs
- Combined forward/backward and turning movements
- Safety stops when tracking is lost

## Project Structure

```
human_track/
├── main.py                    # Application entry point
├── requirements.txt           # Python dependencies
├── config/
│   └── settings.py           # Configuration settings
├── src/
│   ├── camera/
│   │   ├── __init__.py
│   │   └── camera_manager.py # Camera operations and streaming
│   ├── control/
│   │   ├── __init__.py
│   │   └── motor_controller.py # Motor control and movement
│   ├── tracking/
│   │   ├── __init__.py
│   │   └── human_tracker.py  # Human detection and tracking logic
│   └── web/
│       ├── __init__.py
│       └── app.py           # Flask web application
├── static/
│   ├── style.css           # Web interface styling
│   └── script.js           # Frontend JavaScript
├── templates/
│   └── index.html          # Main web interface
└── .github/
    └── copilot-instructions.md # Development guidelines
```

## Troubleshooting

### Common Issues

**Camera not working:**
```bash
# Check camera connection
vcgencmd get_camera

# Test camera
raspistill -v -o test.jpg
```

**Motors not responding:**
- Verify power connections
- Check GPIO pin assignments in `motor_controller.py`
- Ensure PCA9685 I2C connection is stable

**Poor detection performance:**
- Adjust lighting conditions
- Tune `DETECTION_CONFIDENCE_THRESHOLD` in settings
- Check camera focus and positioning

**Network connectivity:**
```bash
# Find Raspberry Pi IP address
hostname -I

# Check if web server is running
curl http://localhost:5000/api/status
```

### Performance Optimization

**For better tracking performance:**
1. Use lower camera resolution (320x240) for faster processing
2. Adjust PID parameters in settings for smoother movement
3. Ensure adequate lighting for better detection
4. Position camera at human chest height for optimal detection

**For system stability:**
1. Use a reliable power supply (2.5A+ recommended)
2. Use high-quality MicroSD card (Class 10+)
3. Ensure proper cooling for Raspberry Pi
4. Monitor system temperature during operation

## Development

### VS Code Tasks

The project includes VS Code tasks for development:

- **Run Human Tracking Car**: Start the application
- **Run Human Tracking Car (Debug)**: Start with debug output
- **Install Dependencies**: Install required packages

### Testing Without Hardware

The project includes simulation modes for development:

```python
# In motor_controller.py
RPI_AVAILABLE = False  # Enables simulation mode

# In camera_manager.py  
PI_CAMERA_AVAILABLE = False  # Uses USB camera fallback
```

### Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Make your changes following the coding guidelines in `.github/copilot-instructions.md`
4. Test thoroughly on hardware
5. Submit a pull request

## Safety Considerations

- **Supervision Required**: Always supervise the car during operation
- **Safe Environment**: Use in open areas away from stairs, obstacles, and fragile items
- **Emergency Stop**: Keep the web interface accessible for immediate stopping
- **Power Management**: Monitor battery levels to prevent unexpected shutdown
- **Speed Limits**: Keep speeds reasonable for safe operation

## Future Enhancements

- [ ] Multiple human tracking and selection
- [ ] Voice control integration
- [ ] Mobile app companion
- [ ] Advanced obstacle avoidance
- [ ] Machine learning-based person identification
- [ ] GPS waypoint navigation
- [ ] Camera pan-tilt control for wider field of view

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Based on the Freenove 4WD Smart Car Kit
- Uses OpenCV computer vision library
- Inspired by autonomous vehicle research
- Thanks to the Raspberry Pi and maker communities

## Support

For questions, issues, or contributions:

1. Check the [Issues](issues) page for known problems
2. Search existing discussions and solutions
3. Create a new issue with detailed description and hardware setup
4. Include logs and error messages when reporting bugs

---

**Happy Tracking! 🚗👁️**