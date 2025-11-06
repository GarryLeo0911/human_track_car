"""
Freenove-compatible Motor Control Module
Based on the official Freenove 4WD Smart Car Kit implementation.
"""

import logging
import time
from threading import Lock

logger = logging.getLogger(__name__)

# Try to import required modules for Raspberry Pi
try:
    import smbus
    I2C_AVAILABLE = True
except ImportError:
    I2C_AVAILABLE = False
    logger.warning("smbus not available - running in simulation mode")

class PCA9685_Freenove:
    """PCA9685 PWM controller based on Freenove implementation."""
    
    # Registers
    __MODE1              = 0x00
    __PRESCALE           = 0xFE
    __LED0_ON_L          = 0x06
    __LED0_ON_H          = 0x07
    __LED0_OFF_L         = 0x08
    __LED0_OFF_H         = 0x09
    __ALLLED_ON_L        = 0xFA
    __ALLLED_ON_H        = 0xFB
    __ALLLED_OFF_L       = 0xFC
    __ALLLED_OFF_H       = 0xFD

    def __init__(self, address: int = 0x40, debug: bool = False):
        self.address = address
        self.debug = debug
        self.simulation_mode = not I2C_AVAILABLE
        
        if not self.simulation_mode:
            try:
                self.bus = smbus.SMBus(1)
                self.write(self.__MODE1, 0x00)
                logger.info("PCA9685 initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize PCA9685: {e}")
                self.simulation_mode = True
        
        if self.simulation_mode:
            logger.info("PCA9685 running in simulation mode")
    
    def write(self, reg: int, value: int) -> None:
        """Writes an 8-bit value to the specified register/address."""
        if not self.simulation_mode:
            self.bus.write_byte_data(self.address, reg, value)
        elif self.debug:
            logger.debug(f"SIM: Write reg {reg:02x} = {value:02x}")
      
    def read(self, reg: int) -> int:
        """Read an unsigned byte from the I2C device."""
        if not self.simulation_mode:
            return self.bus.read_byte_data(self.address, reg)
        else:
            return 0
    
    def set_pwm_freq(self, freq: float) -> None:
        """Sets the PWM frequency."""
        if self.simulation_mode:
            logger.debug(f"SIM: Set PWM frequency to {freq} Hz")
            return
            
        import math
        prescaleval = 25000000.0    # 25MHz
        prescaleval /= 4096.0       # 12-bit
        prescaleval /= float(freq)
        prescaleval -= 1.0
        prescale = math.floor(prescaleval + 0.5)

        oldmode = self.read(self.__MODE1)
        newmode = (oldmode & 0x7F) | 0x10        # sleep
        self.write(self.__MODE1, newmode)        # go to sleep
        self.write(self.__PRESCALE, int(math.floor(prescale)))
        self.write(self.__MODE1, oldmode)
        time.sleep(0.005)
        self.write(self.__MODE1, oldmode | 0x80)

    def set_pwm(self, channel: int, on: int, off: int) -> None:
        """Sets a single PWM channel."""
        if not self.simulation_mode:
            self.write(self.__LED0_ON_L + 4 * channel, on & 0xFF)
            self.write(self.__LED0_ON_H + 4 * channel, on >> 8)
            self.write(self.__LED0_OFF_L + 4 * channel, off & 0xFF)
            self.write(self.__LED0_OFF_H + 4 * channel, off >> 8)
        elif self.debug:
            logger.debug(f"SIM: PWM ch{channel} on={on} off={off}")

    def set_motor_pwm(self, channel: int, duty: int) -> None:
        """Sets the PWM duty cycle for a motor."""
        self.set_pwm(channel, 0, duty)
        if self.simulation_mode:
            logger.info(f"SIM: Motor channel {channel} = {duty}")

    def close(self) -> None:
        """Close the I2C bus."""
        if not self.simulation_mode and hasattr(self, 'bus'):
            self.bus.close()


class FreenoveMotorController:
    """Motor controller compatible with Freenove 4WD Smart Car Kit."""
    
    def __init__(self):
        """Initialize the motor controller."""
        self.lock = Lock()
        
        try:
            self.pwm = PCA9685_Freenove(0x40, debug=True)
            self.pwm.set_pwm_freq(50)
            self.hardware_available = True
            logger.info("Freenove motor controller initialized")
        except Exception as e:
            logger.error(f"Failed to initialize motor controller: {e}")
            self.hardware_available = False
            
        # Motor state
        self.current_speed = 0
        self.current_turn = 0
        self.is_moving = False
        
        # Motor duty cycle range (from Freenove code)
        self.max_duty = 4095
        self.speed_scale = 2000  # Max speed duty cycle from Freenove example
        
    def duty_range(self, duty1, duty2, duty3, duty4):
        """Limit duty cycles to valid range."""
        duties = [duty1, duty2, duty3, duty4]
        for i in range(4):
            if duties[i] > self.max_duty:
                duties[i] = self.max_duty
            elif duties[i] < -self.max_duty:
                duties[i] = -self.max_duty
        return duties
    
    def left_upper_wheel(self, duty):
        """Control left upper wheel (channels 0,1)."""
        if duty > 0:
            self.pwm.set_motor_pwm(0, 0)
            self.pwm.set_motor_pwm(1, duty)
        elif duty < 0:
            self.pwm.set_motor_pwm(1, 0)
            self.pwm.set_motor_pwm(0, abs(duty))
        else:
            self.pwm.set_motor_pwm(0, self.max_duty)
            self.pwm.set_motor_pwm(1, self.max_duty)
    
    def left_lower_wheel(self, duty):
        """Control left lower wheel (channels 2,3)."""
        if duty > 0:
            self.pwm.set_motor_pwm(3, 0)
            self.pwm.set_motor_pwm(2, duty)
        elif duty < 0:
            self.pwm.set_motor_pwm(2, 0)
            self.pwm.set_motor_pwm(3, abs(duty))
        else:
            self.pwm.set_motor_pwm(2, self.max_duty)
            self.pwm.set_motor_pwm(3, self.max_duty)
    
    def right_upper_wheel(self, duty):
        """Control right upper wheel (channels 6,7)."""
        if duty > 0:
            self.pwm.set_motor_pwm(6, 0)
            self.pwm.set_motor_pwm(7, duty)
        elif duty < 0:
            self.pwm.set_motor_pwm(7, 0)
            self.pwm.set_motor_pwm(6, abs(duty))
        else:
            self.pwm.set_motor_pwm(6, self.max_duty)
            self.pwm.set_motor_pwm(7, self.max_duty)
    
    def right_lower_wheel(self, duty):
        """Control right lower wheel (channels 4,5)."""
        if duty > 0:
            self.pwm.set_motor_pwm(4, 0)
            self.pwm.set_motor_pwm(5, duty)
        elif duty < 0:
            self.pwm.set_motor_pwm(5, 0)
            self.pwm.set_motor_pwm(4, abs(duty))
        else:
            self.pwm.set_motor_pwm(4, self.max_duty)
            self.pwm.set_motor_pwm(5, self.max_duty)
    
    def set_motor_model(self, duty1, duty2, duty3, duty4):
        """
        Set all motor duty cycles.
        duty1: left upper wheel
        duty2: left lower wheel  
        duty3: right upper wheel
        duty4: right lower wheel
        """
        duty1, duty2, duty3, duty4 = self.duty_range(duty1, duty2, duty3, duty4)
        
        with self.lock:
            self.left_upper_wheel(duty1)
            self.left_lower_wheel(duty2)
            self.right_upper_wheel(duty3)
            self.right_lower_wheel(duty4)
            
            # Update state
            avg_speed = (duty1 + duty2 + duty3 + duty4) / 4
            self.current_speed = avg_speed / self.speed_scale * 100
            self.is_moving = abs(avg_speed) > 0
            
            logger.info(f"MOTOR: LU={duty1} LL={duty2} RU={duty3} RL={duty4}")
    
    def move_forward(self, speed: float = 50):
        """Move car forward."""
        duty = int(speed / 100.0 * self.speed_scale)
        self.current_turn = 0
        # CORRECTED: Forward should be positive duty (toward human)
        self.set_motor_model(duty, duty, duty, duty)
        logger.info(f"Moving forward at speed {speed}% (duty={duty})")
        
    def move_backward(self, speed: float = 50):
        """Move car backward."""
        duty = int(speed / 100.0 * self.speed_scale)
        self.current_turn = 0
        # CORRECTED: Backward should be negative duty (away from human)
        self.set_motor_model(-duty, -duty, -duty, -duty)
        logger.info(f"Moving backward at speed {speed}% (duty={-duty})")
        
    def turn_left(self, speed: float = 50):
        """Turn car left."""
        duty = int(speed / 100.0 * self.speed_scale)
        self.current_speed = 0
        self.current_turn = -speed
        # CORRECTED: Left turn - left wheels backward, right wheels forward
        self.set_motor_model(-duty, -duty, duty, duty)
        logger.info(f"Turning left at speed {speed}% (duty={duty})")
        
    def turn_right(self, speed: float = 50):
        """Turn car right."""
        duty = int(speed / 100.0 * self.speed_scale)
        self.current_speed = 0
        self.current_turn = speed
        # CORRECTED: Right turn - left wheels forward, right wheels backward  
        self.set_motor_model(duty, duty, -duty, -duty)
        logger.info(f"Turning right at speed {speed}% (duty={duty})")
        
    def move_with_turn(self, forward_speed: float, turn_speed: float):
        """
        Move car with combined forward/backward and turning motion.
        
        Args:
            forward_speed: Forward speed (-100 to 100, positive = forward, negative = backward)
            turn_speed: Turn speed (-100 to 100, negative = left, positive = right)
        """
        # Clamp values
        forward_speed = max(-100, min(100, forward_speed))
        turn_speed = max(-100, min(100, turn_speed))
        
        # Calculate individual motor speeds
        # For turning: left motor slows down for right turn, right motor slows down for left turn
        left_speed = forward_speed - turn_speed   
        right_speed = forward_speed + turn_speed  
        
        # Normalize to prevent values > 100
        max_speed = max(abs(left_speed), abs(right_speed))
        if max_speed > 100:
            left_speed = (left_speed / max_speed) * 100
            right_speed = (right_speed / max_speed) * 100
        
        # Convert to duty cycles (CORRECTED: positive duty = forward, negative duty = backward)
        left_duty = int(left_speed / 100.0 * self.speed_scale)  
        right_duty = int(right_speed / 100.0 * self.speed_scale)  
        
        self.current_speed = forward_speed
        self.current_turn = turn_speed
        self.set_motor_model(left_duty, left_duty, right_duty, right_duty)
        logger.info(f"Move+Turn: forward={forward_speed:+.0f}, turn={turn_speed:+.0f} -> L={left_speed:+.0f}, R={right_speed:+.0f}")
        logger.info(f"Motor duties: L={left_duty:+d}, R={right_duty:+d}")
        
        
    def stop(self):
        """Stop all motors."""
        self.current_speed = 0
        self.current_turn = 0
        self.set_motor_model(0, 0, 0, 0)
        logger.info("All motors stopped")
        
    def get_status(self) -> dict:
        """Get current motor status."""
        return {
            'current_speed': self.current_speed,
            'current_turn': self.current_turn,
            'is_moving': self.is_moving,
            'rpi_mode': self.hardware_available,
            'hardware_available': self.hardware_available
        }
        
    def cleanup(self):
        """Clean up motor controller resources."""
        self.stop()
        if hasattr(self, 'pwm'):
            self.pwm.close()
        logger.info("Freenove motor controller cleaned up")


# Test the motor controller
if __name__ == '__main__':
    motor = FreenoveMotorController()
    
    try:
        print("Testing Freenove motor controller...")
        
        print("Forward...")
        motor.move_forward(50)
        time.sleep(1)
        
        print("Backward...")
        motor.move_backward(50)
        time.sleep(1)
        
        print("Left...")
        motor.turn_left(50)
        time.sleep(1)
        
        print("Right...")
        motor.turn_right(50)
        time.sleep(1)
        
        print("Combined movement...")
        motor.move_with_turn(30, 20)
        time.sleep(1)
        
        print("Stop...")
        motor.stop()
        
    except KeyboardInterrupt:
        print("\nTest interrupted")
    finally:
        motor.cleanup()
        print("Test completed")