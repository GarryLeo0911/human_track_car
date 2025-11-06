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

# Tracking settings - ULTRA GENTLE FOR VERY SMOOTH MOVEMENT
TARGET_HUMAN_HEIGHT = 150  # Target height in pixels (distance control)
FRAME_CENTER_DEADZONE = 60  # Further increased from 40 for less twitchy movement
DISTANCE_DEADZONE = 30  # Further increased for stable distance control

# PID Controller settings - ULTRA GENTLE FOR VERY SMOOTH MOVEMENT
PID_X_KP = 0.15  # Further reduced from 0.25 for ultra-gentle turning
PID_X_KI = 0.005  # Further reduced integral gain
PID_X_KD = 0.05  # Reduced derivative gain

PID_DISTANCE_KP = 0.12  # Further reduced from 0.20 for ultra-gentle forward/back
PID_DISTANCE_KI = 0.002  # Further reduced integral gain
PID_DISTANCE_KD = 0.03  # Reduced derivative gain

# Motor settings - ULTRA GENTLE FOR VERY SMOOTH MOVEMENT
MAX_SPEED = 35  # Further reduced from 50 for ultra-gentle movement
MAX_TURN_SPEED = 25  # Further reduced from 35 for ultra-gentle turning
MOTOR_DEADZONE = 5  # Minimum speed to overcome motor friction

# Step-by-step turning settings for ultra-smooth movement
STEP_TURN_ENABLED = True
TURN_STEP_DURATION = 0.3  # Seconds per turn step
TURN_PAUSE_DURATION = 0.2  # Pause between steps to reassess
TURN_STEP_SPEED_FACTOR = 0.4  # Fraction of max speed for step turns

# Web interface settings
WEB_HOST = '0.0.0.0'
WEB_PORT = 5000
WEB_DEBUG = False

# Logging settings
LOG_LEVEL = 'INFO'  # DEBUG, INFO, WARNING, ERROR
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'