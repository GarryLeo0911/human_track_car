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

# Tracking settings - IMPROVED FOR ACCURACY
TARGET_HUMAN_HEIGHT = 150  # Target height in pixels (distance control)
FRAME_CENTER_DEADZONE = 25  # Reduced for more responsive centering
DISTANCE_DEADZONE = 15  # Reduced for more responsive distance control

# PID Controller settings - TUNED FOR ACCURACY
PID_X_KP = 0.4  # Reduced proportional gain for smoother turning
PID_X_KI = 0.02  # Reduced integral gain to prevent oscillation
PID_X_KD = 0.15  # Increased derivative gain for stability

PID_DISTANCE_KP = 0.25  # Reduced proportional gain for smoother forward/back
PID_DISTANCE_KI = 0.01  # Reduced integral gain to prevent oscillation
PID_DISTANCE_KD = 0.08  # Increased derivative gain for stability

# Motor settings
MAX_SPEED = 100  # Maximum motor speed percentage
MAX_TURN_SPEED = 100  # Maximum turning speed percentage
MOTOR_DEADZONE = 5  # Minimum speed to overcome motor friction

# Web interface settings
WEB_HOST = '0.0.0.0'
WEB_PORT = 5000
WEB_DEBUG = False

# Logging settings
LOG_LEVEL = 'INFO'  # DEBUG, INFO, WARNING, ERROR
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'