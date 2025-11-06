"""
Motor Control Module
Handles 4WD motor control for the tracking car.
"""

import logging
import time
from threading import Lock

# Try to import Raspberry Pi specific modules
# Prefer gpiozero for Ubuntu compatibility
try:
    # First try gpiozero (better Ubuntu support)
    import gpiozero
    GPIO_LIB = 'gpiozero'
    GPIO_AVAILABLE = True
except ImportError:
    try:
        # Fallback to RPi.GPIO
        import RPi.GPIO as GPIO
        GPIO_LIB = 'RPi.GPIO'
        GPIO_AVAILABLE = True
    except ImportError:
        GPIO_LIB = None
        GPIO_AVAILABLE = False

# Try to import PCA9685 and motor control
try:
    from adafruit_pca9685 import PCA9685
    from adafruit_motor import motor
    import board
    import busio
    PCA9685_AVAILABLE = True
except ImportError:
    PCA9685_AVAILABLE = False

# Overall hardware availability
RPI_AVAILABLE = GPIO_AVAILABLE and PCA9685_AVAILABLE

if not RPI_AVAILABLE:
    logging.warning(f"Hardware modules not fully available. GPIO: {GPIO_AVAILABLE}, PCA9685: {PCA9685_AVAILABLE}. Running in simulation mode.")

logger = logging.getLogger(__name__)

class MotorController:
    """4WD Motor controller for the tracking car."""
    
    def __init__(self):
        """Initialize the motor controller."""
        self.lock = Lock()
        self.rpi_mode = RPI_AVAILABLE
        
        if self.rpi_mode:
            self._init_rpi_hardware()
        else:
            self._init_simulation_mode()
            
        # Motor state
        self.current_speed = 0
        self.current_turn = 0
        self.is_moving = False
        
    def _init_rpi_hardware(self):
        """Initialize Raspberry Pi hardware."""
        try:
            # Initialize I2C bus
            i2c = busio.I2C(board.SCL, board.SDA)
            
            # Initialize PCA9685 PWM controller
            self.pca = PCA9685(i2c)
            self.pca.frequency = 60
            
            # Define motor pins (adjust based on your wiring)
            # Left motors
            self.motor_left_front = motor.DCMotor(self.pca.channels[0], self.pca.channels[1])
            self.motor_left_rear = motor.DCMotor(self.pca.channels[2], self.pca.channels[3])
            
            # Right motors  
            self.motor_right_front = motor.DCMotor(self.pca.channels[4], self.pca.channels[5])
            self.motor_right_rear = motor.DCMotor(self.pca.channels[6], self.pca.channels[7])
            
            self.motors = [
                self.motor_left_front,
                self.motor_left_rear,
                self.motor_right_front,
                self.motor_right_rear
            ]
            
            logger.info("Motor controller initialized in RPI mode")
            
        except Exception as e:
            logger.error(f"Failed to initialize RPI hardware: {e}")
            self.rpi_mode = False
            self._init_simulation_mode()
            
    def _init_simulation_mode(self):
        """Initialize simulation mode for testing."""
        logger.info("Motor controller initialized in simulation mode")
        logger.info("Motor commands will be logged but not executed on real hardware")
        self.motors = None
        
    def move_forward(self, speed: float = 50):
        """
        Move car forward.
        
        Args:
            speed: Speed percentage (0-100)
        """
        with self.lock:
            speed = max(0, min(100, speed))
            self.current_speed = speed
            self.current_turn = 0
            self.is_moving = speed > 0
            
            if self.rpi_mode and self.motors:
                throttle = speed / 100.0
                for motor in self.motors:
                    motor.throttle = throttle
            else:
                logger.info(f"SIM: Moving forward at speed {speed}%")
                
    def move_backward(self, speed: float = 50):
        """
        Move car backward.
        
        Args:
            speed: Speed percentage (0-100)
        """
        with self.lock:
            speed = max(0, min(100, speed))
            self.current_speed = -speed
            self.current_turn = 0
            self.is_moving = speed > 0
            
            if self.rpi_mode and self.motors:
                throttle = -speed / 100.0
                for motor in self.motors:
                    motor.throttle = throttle
            else:
                logger.info(f"SIM: Moving backward at speed {speed}%")
                
    def turn_left(self, speed: float = 50):
        """
        Turn car left.
        
        Args:
            speed: Turn speed percentage (0-100)
        """
        with self.lock:
            speed = max(0, min(100, speed))
            self.current_turn = -speed
            self.is_moving = speed > 0
            
            if self.rpi_mode and self.motors:
                throttle = speed / 100.0
                # Left motors backward, right motors forward
                self.motor_left_front.throttle = -throttle
                self.motor_left_rear.throttle = -throttle
                self.motor_right_front.throttle = throttle
                self.motor_right_rear.throttle = throttle
            else:
                logger.info(f"SIM: Turning left at speed {speed}%")
                
    def turn_right(self, speed: float = 50):
        """
        Turn car right.
        
        Args:
            speed: Turn speed percentage (0-100)
        """
        with self.lock:
            speed = max(0, min(100, speed))
            self.current_turn = speed
            self.is_moving = speed > 0
            
            if self.rpi_mode and self.motors:
                throttle = speed / 100.0
                # Left motors forward, right motors backward
                self.motor_left_front.throttle = throttle
                self.motor_left_rear.throttle = throttle
                self.motor_right_front.throttle = -throttle
                self.motor_right_rear.throttle = -throttle
            else:
                logger.info(f"SIM: Turning right at speed {speed}%")
                
    def move_with_turn(self, forward_speed: float, turn_speed: float):
        """
        Move car with combined forward/backward and turning motion.
        
        Args:
            forward_speed: Forward speed (-100 to 100, negative = backward)
            turn_speed: Turn speed (-100 to 100, negative = left, positive = right)
        """
        with self.lock:
            # Clamp values
            forward_speed = max(-100, min(100, forward_speed))
            turn_speed = max(-100, min(100, turn_speed))
            
            self.current_speed = forward_speed
            self.current_turn = turn_speed
            self.is_moving = abs(forward_speed) > 0 or abs(turn_speed) > 0
            
            if self.rpi_mode and self.motors:
                # Calculate individual motor speeds
                left_speed = forward_speed - turn_speed
                right_speed = forward_speed + turn_speed
                
                # Normalize to prevent values > 100
                max_speed = max(abs(left_speed), abs(right_speed))
                if max_speed > 100:
                    left_speed = (left_speed / max_speed) * 100
                    right_speed = (right_speed / max_speed) * 100
                
                # Convert to throttle values
                left_throttle = left_speed / 100.0
                right_throttle = right_speed / 100.0
                
                # Apply to motors
                self.motor_left_front.throttle = left_throttle
                self.motor_left_rear.throttle = left_throttle
                self.motor_right_front.throttle = right_throttle
                self.motor_right_rear.throttle = right_throttle
                
            else:
                logger.info(f"SIM: Moving - Forward: {forward_speed}%, Turn: {turn_speed}%")
                
    def stop(self):
        """Stop all motors."""
        with self.lock:
            self.current_speed = 0
            self.current_turn = 0
            self.is_moving = False
            
            if self.rpi_mode and self.motors:
                for motor in self.motors:
                    motor.throttle = 0
            else:
                logger.info("SIM: Stopping all motors")
                
    def get_status(self) -> dict:
        """Get current motor status."""
        with self.lock:
            return {
                'current_speed': self.current_speed,
                'current_turn': self.current_turn,
                'is_moving': self.is_moving,
                'rpi_mode': self.rpi_mode
            }
            
    def cleanup(self):
        """Clean up motor controller resources."""
        self.stop()
        
        if self.rpi_mode:
            try:
                if hasattr(self, 'pca'):
                    self.pca.deinit()
            except Exception as e:
                logger.error(f"Error during cleanup: {e}")
                
        logger.info("Motor controller cleaned up")


class ServoController:
    """Servo controller for camera pan/tilt (optional enhancement)."""
    
    def __init__(self, pan_channel: int = 8, tilt_channel: int = 9):
        """
        Initialize servo controller.
        
        Args:
            pan_channel: PWM channel for pan servo
            tilt_channel: PWM channel for tilt servo
        """
        self.rpi_mode = RPI_AVAILABLE
        self.pan_angle = 90  # Center position
        self.tilt_angle = 90  # Center position
        
        if self.rpi_mode:
            try:
                # Initialize I2C and PCA9685 for servos
                i2c = busio.I2C(board.SCL, board.SDA)
                self.pca = PCA9685(i2c)
                self.pca.frequency = 60
                
                self.pan_channel = pan_channel
                self.tilt_channel = tilt_channel
                
                # Set initial position
                self.set_pan_tilt(90, 90)
                
                logger.info("Servo controller initialized")
                
            except Exception as e:
                logger.error(f"Failed to initialize servo controller: {e}")
                self.rpi_mode = False
        else:
            logger.info("Servo controller initialized in simulation mode")
            
    def set_pan_tilt(self, pan_angle: float, tilt_angle: float):
        """
        Set pan and tilt angles.
        
        Args:
            pan_angle: Pan angle (0-180 degrees)
            tilt_angle: Tilt angle (0-180 degrees)
        """
        # Clamp angles
        pan_angle = max(0, min(180, pan_angle))
        tilt_angle = max(0, min(180, tilt_angle))
        
        self.pan_angle = pan_angle
        self.tilt_angle = tilt_angle
        
        if self.rpi_mode:
            try:
                # Convert angle to PWM duty cycle
                pan_duty = int((pan_angle / 180.0) * 65535)
                tilt_duty = int((tilt_angle / 180.0) * 65535)
                
                self.pca.channels[self.pan_channel].duty_cycle = pan_duty
                self.pca.channels[self.tilt_channel].duty_cycle = tilt_duty
                
            except Exception as e:
                logger.error(f"Error setting servo position: {e}")
        else:
            logger.debug(f"SIM: Pan: {pan_angle}°, Tilt: {tilt_angle}°")
            
    def cleanup(self):
        """Clean up servo controller."""
        if self.rpi_mode and hasattr(self, 'pca'):
            try:
                self.pca.deinit()
            except Exception as e:
                logger.error(f"Error during servo cleanup: {e}")
                
        logger.info("Servo controller cleaned up")