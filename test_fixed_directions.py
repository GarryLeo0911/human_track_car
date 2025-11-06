#!/usr/bin/env python3
"""
Test Fixed Motor Directions
Verify that the motor direction fix resolves the avoidance behavior.
"""

import sys
import os
import time

# Add src directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.control.freenove_motor_controller import FreenoveMotorController

def test_fixed_directions():
    """Test the fixed motor directions."""
    
    print("Testing FIXED Motor Directions")
    print("=" * 40)
    print("This tests the corrected motor logic that should fix the avoidance behavior.")
    print("")
    
    try:
        motor = FreenoveMotorController()
        
        # Test scenarios that occur during human tracking
        tracking_scenarios = [
            {
                "name": "Human TOO FAR - Robot should APPROACH (follow)",
                "description": "When human is far (small in frame), robot should move FORWARD",
                "forward_speed": 30,  # Positive = should move toward human
                "turn_speed": 0,
                "expected_behavior": "Move FORWARD (positive duty cycles)"
            },
            {
                "name": "Human TOO CLOSE - Robot should RETREAT", 
                "description": "When human is close (large in frame), robot should move BACKWARD",
                "forward_speed": -30,  # Negative = should move away from human
                "turn_speed": 0,
                "expected_behavior": "Move BACKWARD (negative duty cycles)"
            },
            {
                "name": "Human to RIGHT - Robot should TURN RIGHT",
                "description": "When human is right of center, robot should turn RIGHT",
                "forward_speed": 0,
                "turn_speed": 30,  # Positive = turn right
                "expected_behavior": "Turn RIGHT (left wheels faster)"
            },
            {
                "name": "Human to LEFT - Robot should TURN LEFT",
                "description": "When human is left of center, robot should turn LEFT", 
                "forward_speed": 0,
                "turn_speed": -30,  # Negative = turn left
                "expected_behavior": "Turn LEFT (right wheels faster)"
            },
            {
                "name": "Human FAR and RIGHT - Combined movement",
                "description": "Human is far and to the right",
                "forward_speed": 25,
                "turn_speed": 20,
                "expected_behavior": "Move FORWARD + Turn RIGHT"
            }
        ]
        
        print("Testing corrected tracking scenarios:")
        print("-" * 50)
        
        for i, scenario in enumerate(tracking_scenarios, 1):
            print(f"\n{i}. {scenario['name']}")
            print(f"   Situation: {scenario['description']}")
            print(f"   Command: move_with_turn({scenario['forward_speed']}, {scenario['turn_speed']})")
            print(f"   Expected: {scenario['expected_behavior']}")
            print("   Executing...")
            
            # Execute the command
            motor.move_with_turn(scenario['forward_speed'], scenario['turn_speed'])
            print("   ↑ Check the motor log output above ↑")
            
            # Stop after each test
            motor.stop()
            time.sleep(0.5)
        
        print(f"\n{'='*50}")
        print("MOTOR DIRECTION TEST COMPLETED")
        print(f"{'='*50}")
        print("Key indicators of success:")
        print("1. Positive forward_speed → Positive duty cycles (toward human)")
        print("2. Negative forward_speed → Negative duty cycles (away from human)") 
        print("3. Positive turn_speed → Right turn (left motor > right motor)")
        print("4. Negative turn_speed → Left turn (right motor > left motor)")
        print("")
        print("If the log shows these patterns, the avoidance behavior should be FIXED!")
        
    except Exception as e:
        print(f"Error during test: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if 'motor' in locals():
            motor.cleanup()

def test_specific_avoidance_scenario():
    """Test the specific scenario where robot was avoiding."""
    
    print("\nTesting Specific Avoidance Scenario")
    print("=" * 40)
    
    try:
        motor = FreenoveMotorController()
        
        # Simulate the exact scenario: human is detected, robot should follow
        print("Scenario: Human detected in front, slightly far away")
        print("- Human height: 120 pixels (target: 150)")
        print("- Human center: 320 pixels (target: 320)")
        print("- Expected: Robot should move FORWARD to get closer")
        print("")
        
        # Calculate what the tracking algorithm would do
        target_distance = 150
        target_x = 320
        human_height = 120  # Too far
        center_x = 320      # Centered
        
        # Calculate errors (same as tracking algorithm)
        x_error = center_x - target_x  # 0 (centered)
        distance_error = target_distance - human_height  # +30 (too far)
        
        print(f"Tracking calculation:")
        print(f"  x_error = {x_error} (centered)")
        print(f"  distance_error = {distance_error} (human too far)")
        
        # PID response (simplified)
        kp_speed = 0.35
        kp_turn = 0.5
        
        speed_output = kp_speed * distance_error  # Should be positive
        turn_output = kp_turn * x_error           # Should be zero
        
        forward_speed = max(-100, min(100, speed_output))
        turn_speed = max(-100, min(100, turn_output))
        
        print(f"  PID output: forward_speed = {forward_speed}, turn_speed = {turn_speed}")
        print(f"  Expected: Robot moves FORWARD (positive forward_speed)")
        print("")
        
        print("Executing corrected motor command...")
        motor.move_with_turn(forward_speed, turn_speed)
        
        print("\nIf the motor log shows POSITIVE duty cycles, the fix worked!")
        print("If it shows NEGATIVE duty cycles, robot would still avoid.")
        
        motor.stop()
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        motor.cleanup()

if __name__ == "__main__":
    test_fixed_directions()
    test_specific_avoidance_scenario()