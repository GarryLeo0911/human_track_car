# Human Tracking Car Configuration

# Camera settings
CAMERA_RESOLUTION = (640, 480)
CAMERA_FRAMERATE = 30
USE_PI_CAMERA = False  # Set to True to use Pi Camera, False for USB camera (safer for Ubuntu)

# Detection settings - IMPROVED FOR ACCURACY
DETECTION_CONFIDENCE_THRESHOLD = 0.4  # Increased from 0.5 for better filtering
MIN_DETECTION_SIZE = (30, 60)  # Adjusted minimum width, height for valid detection
MAX_DETECTION_SIZE = (300, 400)  # Added maximum size to filter out false positives
MIN_ASPECT_RATIO = 1.5  # Minimum height/width ratio for human-like shapes
MAX_ASPECT_RATIO = 4.0  # Maximum height/width ratio for human-like shapes

# Tracking settings - TUNED FOR SMOOTH MOVEMENT
TARGET_HUMAN_HEIGHT = 150  # Target height in pixels (distance control)
FRAME_CENTER_DEADZONE = 40  # Increased from 25 for less twitchy movement
DISTANCE_DEADZONE = 20  # Pixel height difference to avoid jittery movement

# PID Controller settings - REDUCED FOR GENTLE MOVEMENT
PID_X_KP = 0.25  # Reduced from 0.4 for gentler turning
PID_X_KI = 0.01  # Reduced integral gain to prevent oscillation
PID_X_KD = 0.08  # Derivative gain for stability

PID_DISTANCE_KP = 0.20  # Reduced from 0.25 for gentler forward/back
PID_DISTANCE_KI = 0.005  # Reduced integral gain to prevent oscillation
PID_DISTANCE_KD = 0.05  # Derivative gain for stability

# Motor settings - REDUCED FOR SMOOTH MOVEMENT
MAX_SPEED = 50  # Reduced from 100 for gentler movement
MAX_TURN_SPEED = 35  # Reduced from 100 for smoother turning
MOTOR_DEADZONE = 5  # Minimum speed to overcome motor friction

# Web interface settings
WEB_HOST = '0.0.0.0'
WEB_PORT = 5000
WEB_DEBUG = False

# Logging settings
LOG_LEVEL = 'INFO'  # DEBUG, INFO, WARNING, ERROR
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'