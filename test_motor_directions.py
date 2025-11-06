#!/usr/bin/env python3
"""
Test script to verify motor directions are working correctly.
This will help diagnose if the car is moving in the right direction.
"""

import time
import sys
import os

# Add src directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from control.freenove_motor_controller import FreenoveMotorController

def test_motor_directions():
    """Test all motor directions to verify they work as expected."""
    
    print("Testing Freenove Motor Controller Directions")
    print("=" * 50)
    
    motor = FreenoveMotorController()
    
    try:
        print("\n1. Testing FORWARD movement (should move toward you)...")
        motor.move_with_turn(forward_speed=30, turn_speed=0)
        time.sleep(2)
        motor.stop()
        
        print("\n2. Testing BACKWARD movement (should move away from you)...")
        motor.move_with_turn(forward_speed=-30, turn_speed=0)
        time.sleep(2)
        motor.stop()
        
        print("\n3. Testing LEFT turn (should turn left)...")
        motor.move_with_turn(forward_speed=0, turn_speed=-30)
        time.sleep(2)
        motor.stop()
        
        print("\n4. Testing RIGHT turn (should turn right)...")
        motor.move_with_turn(forward_speed=0, turn_speed=30)
        time.sleep(2)
        motor.stop()
        
        print("\n5. Testing FORWARD + RIGHT (move forward while turning right)...")
        motor.move_with_turn(forward_speed=30, turn_speed=30)
        time.sleep(2)
        motor.stop()
        
        print("\n6. Testing tracking scenario: Human too far (should move forward)...")
        # Simulate: target_distance=150, human_height=100 (too far)
        # distance_error = 150 - 100 = 50 (positive)
        # PID output would be positive, so forward_speed should be positive
        forward_speed = 40  # Positive = forward
        turn_speed = 0
        print(f"   Simulating: distance_error=+50 → forward_speed={forward_speed}")
        motor.move_with_turn(forward_speed, turn_speed)
        time.sleep(2)
        motor.stop()
        
        print("\n7. Testing tracking scenario: Human too close (should move backward)...")
        # Simulate: target_distance=150, human_height=200 (too close)  
        # distance_error = 150 - 200 = -50 (negative)
        # PID output would be negative, so forward_speed should be negative
        forward_speed = -40  # Negative = backward
        turn_speed = 0
        print(f"   Simulating: distance_error=-50 → forward_speed={forward_speed}")
        motor.move_with_turn(forward_speed, turn_speed)
        time.sleep(2)
        motor.stop()
        
        print("\n8. Testing tracking scenario: Human to the right (should turn right)...")
        # Simulate: target_x=320, center_x=400 (human right of center)
        # x_error = 400 - 320 = 80 (positive)
        # PID output would be positive, so turn_speed should be positive (right)
        forward_speed = 0
        turn_speed = 30  # Positive = right
        print(f"   Simulating: x_error=+80 → turn_speed={turn_speed}")
        motor.move_with_turn(forward_speed, turn_speed)
        time.sleep(2)
        motor.stop()
        
        print("\nTest completed! Check if all movements matched the descriptions.")
        print("If any movement was wrong, we'll need to adjust the motor logic.")
        
    except KeyboardInterrupt:
        print("\nTest interrupted by user")
    except Exception as e:
        print(f"\nError during test: {e}")
    finally:
        motor.cleanup()
        print("Motor controller cleaned up")

if __name__ == "__main__":
    test_motor_directions()