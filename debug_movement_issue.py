#!/usr/bin/env python3
"""
Debug Movement Issues
Test script to diagnose why tracking doesn't move and direction issues.
"""

import logging
import time
import sys
import os

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.control.freenove_motor_controller import FreenoveMotorController

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

def test_motor_directions():
    """Test motor directions to identify forward/backward issue."""
    logger.info("=== TESTING MOTOR DIRECTIONS ===")
    
    motor = FreenoveMotorController()
    
    try:
        print("\nTesting individual motor directions...")
        print("(Check if these match expected physical movement)")
        
        # Test forward
        print("\n1. FORWARD test (robot should move TOWARD human/forward)")
        motor.move_forward(30)
        print("   -> Expected: Robot moves forward")
        print("   -> Actual direction: (observe robot)")
        time.sleep(2)
        motor.stop()
        time.sleep(1)
        
        # Test backward  
        print("\n2. BACKWARD test (robot should move AWAY from human/backward)")
        motor.move_backward(30)
        print("   -> Expected: Robot moves backward")
        print("   -> Actual direction: (observe robot)")
        time.sleep(2)
        motor.stop()
        time.sleep(1)
        
        # Test left turn
        print("\n3. LEFT TURN test")
        motor.turn_left(30)
        print("   -> Expected: Robot turns left (counterclockwise)")
        print("   -> Actual direction: (observe robot)")
        time.sleep(2)
        motor.stop()
        time.sleep(1)
        
        # Test right turn
        print("\n4. RIGHT TURN test")
        motor.turn_right(30)
        print("   -> Expected: Robot turns right (clockwise)")
        print("   -> Actual direction: (observe robot)")
        time.sleep(2)
        motor.stop()
        time.sleep(1)
        
        print("\nDone with direction tests.")
        
    except KeyboardInterrupt:
        print("\nTest interrupted")
    finally:
        motor.stop()
        motor.cleanup()

def test_tracking_movement_logic():
    """Test the specific movement logic used by tracking."""
    logger.info("=== TESTING TRACKING MOVEMENT LOGIC ===")
    
    motor = FreenoveMotorController()
    
    try:
        print("\nTesting move_with_turn() function used by tracking...")
        
        # Test scenarios that tracking would generate
        scenarios = [
            (20, 0, "Forward only (human too far)"),
            (-15, 0, "Backward only (human too close)"), 
            (0, 10, "Right turn only (human to the right)"),
            (0, -10, "Left turn only (human to the left)"),
            (15, 5, "Forward + slight right (human far and slightly right)"),
            (10, -8, "Forward + slight left (human far and slightly left)"),
        ]
        
        for forward_speed, turn_speed, description in scenarios:
            print(f"\n{description}")
            print(f"  Calling: move_with_turn({forward_speed}, {turn_speed})")
            motor.move_with_turn(forward_speed, turn_speed)
            print(f"  Expected: {description}")
            print(f"  Actual: (observe robot movement)")
            time.sleep(2)
            motor.stop()
            time.sleep(1)
            
        print("\nDone with tracking movement tests.")
        
    except KeyboardInterrupt:
        print("\nTest interrupted")
    finally:
        motor.stop()
        motor.cleanup()

def test_minimum_speeds():
    """Test if very low speeds work (tracking uses low speeds)."""
    logger.info("=== TESTING MINIMUM SPEEDS ===")
    
    motor = FreenoveMotorController()
    
    try:
        print("\nTesting very low speeds (tracking uses these ranges)...")
        
        speeds = [5, 10, 15, 20, 25, 30]
        
        for speed in speeds:
            print(f"\nTesting forward at {speed}% speed")
            motor.move_forward(speed)
            print(f"  Does robot move? (observe)")
            time.sleep(1.5)
            motor.stop()
            time.sleep(0.5)
            
        print("\nDone with minimum speed tests.")
        
    except KeyboardInterrupt:
        print("\nTest interrupted")
    finally:
        motor.stop()
        motor.cleanup()

def simulate_tracking_behavior():
    """Simulate what tracking does when it detects a human."""
    logger.info("=== SIMULATING TRACKING BEHAVIOR ===")
    
    motor = FreenoveMotorController()
    
    try:
        print("\nSimulating tracking scenarios...")
        
        # Scenario 1: Human detected in center, too far
        print("\n1. Human in center, too far away")
        print("   Expected: Move forward to get closer")
        motor.move_with_turn(25, 0)  # Values similar to what tracking uses
        time.sleep(2)
        motor.stop()
        time.sleep(1)
        
        # Scenario 2: Human detected in center, too close  
        print("\n2. Human in center, too close")
        print("   Expected: Move backward to maintain distance")
        motor.move_with_turn(-20, 0)
        time.sleep(2)
        motor.stop()
        time.sleep(1)
        
        # Scenario 3: Human to the right, good distance
        print("\n3. Human to the right, good distance")
        print("   Expected: Turn right to center human")
        motor.move_with_turn(0, 15)
        time.sleep(2)
        motor.stop()
        time.sleep(1)
        
        # Scenario 4: Human to the left, too far
        print("\n4. Human to the left and too far")
        print("   Expected: Move forward while turning left")
        motor.move_with_turn(20, -12)
        time.sleep(2)
        motor.stop()
        time.sleep(1)
        
        print("\nDone with tracking simulation.")
        
    except KeyboardInterrupt:
        print("\nTest interrupted")
    finally:
        motor.stop()
        motor.cleanup()

def main():
    """Run all movement tests."""
    print("HUMAN TRACKING CAR - MOVEMENT DEBUG TOOL")
    print("="*50)
    print("\nThis tool will test motor movements to diagnose issues:")
    print("1. Direction correctness (forward/backward swapped?)")
    print("2. Low-speed movement capability")
    print("3. Tracking-specific movement patterns")
    print("\nWatch the robot and confirm movements match expectations!")
    print("\nPress Ctrl+C at any time to stop.")
    
    input("\nPress Enter to start tests...")
    
    # Run all tests
    test_motor_directions()
    input("\nPress Enter to continue to tracking movement tests...")
    
    test_tracking_movement_logic()
    input("\nPress Enter to continue to minimum speed tests...")
    
    test_minimum_speeds()
    input("\nPress Enter to continue to tracking simulation...")
    
    simulate_tracking_behavior()
    
    print("\n" + "="*50)
    print("ALL TESTS COMPLETED")
    print("\nBased on your observations:")
    print("1. If forward/backward are swapped, we need to fix motor controller")
    print("2. If robot doesn't move at low speeds, we need to increase minimum speeds")
    print("3. If tracking movements don't work, we need to debug tracking logic")

if __name__ == "__main__":
    main()