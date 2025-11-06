# Human Tracking Car Configuration

# Camera settings
CAMERA_RESOLUTION = (640, 480)
CAMERA_FRAMERATE = 30
USE_PI_CAMERA = True  # Set to False to use USB camera

# Detection settings
DETECTION_CONFIDENCE_THRESHOLD = 0.5
MIN_DETECTION_SIZE = (50, 100)  # Minimum width, height for valid detection

# Tracking settings
TARGET_HUMAN_HEIGHT = 150  # Target height in pixels (distance control)
FRAME_CENTER_DEADZONE = 30  # Pixels around center to avoid jittery movement
DISTANCE_DEADZONE = 20  # Pixel height difference to avoid jittery movement

# PID Controller settings
PID_X_KP = 0.5  # Proportional gain for X-axis (turning)
PID_X_KI = 0.1  # Integral gain for X-axis
PID_X_KD = 0.2  # Derivative gain for X-axis

PID_DISTANCE_KP = 0.3  # Proportional gain for distance (forward/backward)
PID_DISTANCE_KI = 0.05  # Integral gain for distance
PID_DISTANCE_KD = 0.1  # Derivative gain for distance

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