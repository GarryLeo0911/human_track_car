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

# Tracking settings - PERCENTAGE-BASED DISTANCE CONTROL
TARGET_HUMAN_HEIGHT = 120  # Fallback target height in pixels
TARGET_HUMAN_PERCENTAGE = 0.25  # Human should occupy 25% of frame height (120/480)
FRAME_CENTER_DEADZONE = 40  # Reduced from 60 for better centering response
DISTANCE_DEADZONE = 15  # Percentage deadzone (1.5% of frame height)
EDGE_THRESHOLD = 100  # Pixels from edge to trigger aggressive turning

# PID Controller settings - INCREASED TURNING RESPONSIVENESS
PID_X_KP = 0.25  # Increased from 0.15 for stronger turning response
PID_X_KI = 0.008  # Slightly increased integral gain
PID_X_KD = 0.08  # Increased derivative gain for stability

PID_DISTANCE_KP = 0.12  # Keep distance PID gentle
PID_DISTANCE_KI = 0.002  # Keep distance PID gentle
PID_DISTANCE_KD = 0.03  # Keep distance PID gentle

# Motor settings - INCREASED TURNING POWER TO OVERCOME RESISTANCE  
MAX_SPEED = 60  # Increased from 35 to overcome resistance
MAX_TURN_SPEED = 70  # Further increased from 45 for stronger turning force
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