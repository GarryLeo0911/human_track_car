<!-- Use this file to provide workspace-specific custom instructions to Copilot. For more details, visit https://code.visualstudio.com/docs/copilot/copilot-customization#_use-a-githubcopilotinstructionsmd-file -->

# Human Tracking Car Project

This project creates an automatic human tracking car based on the Freenove 4WD Smart Car Kit for Raspberry Pi. The car uses computer vision to detect and follow humans while keeping them centered in the camera frame.

## Project Components
- Python-based server with Flask web interface
- OpenCV computer vision for human detection and tracking
- Motor control system for 4WD movement
- Real-time video streaming with detection overlay
- PID control for smooth tracking movements

## Development Guidelines
- Use OpenCV for human detection (HOG descriptor or YOLO)
- Implement PID control for smooth car movements
- Maintain modular code structure separating concerns
- Follow Python best practices and include proper error handling
- Ensure real-time performance for responsive tracking