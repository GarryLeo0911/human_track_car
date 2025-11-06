#!/usr/bin/env python3
"""
Simple logic test to verify tracking calculations.
"""

def test_tracking_logic():
    """Test the tracking logic without hardware."""
    
    print("Testing Human Tracking Logic")
    print("=" * 40)
    
    # Constants from the tracker
    target_distance = 150  # Target human height in pixels
    target_x = 320         # Center of 640px wide frame
    
    # Test scenarios
    scenarios = [
        {
            "name": "Human too far away",
            "human_height": 100,
            "center_x": 320,
            "expected": "Move FORWARD"
        },
        {
            "name": "Human too close", 
            "human_height": 200,
            "center_x": 320,
            "expected": "Move BACKWARD"
        },
        {
            "name": "Human right of center",
            "human_height": 150,
            "center_x": 400,
            "expected": "Turn RIGHT"
        },
        {
            "name": "Human left of center",
            "human_height": 150,
            "center_x": 240,
            "expected": "Turn LEFT"
        },
        {
            "name": "Human perfect position",
            "human_height": 150,
            "center_x": 320,
            "expected": "STOP (no movement)"
        },
        {
            "name": "Human far and right",
            "human_height": 80,
            "center_x": 450,
            "expected": "Move FORWARD + Turn RIGHT"
        }
    ]
    
    for i, scenario in enumerate(scenarios, 1):
        print(f"\n{i}. {scenario['name']}")
        print(f"   Human height: {scenario['human_height']} (target: {target_distance})")
        print(f"   Human center X: {scenario['center_x']} (target: {target_x})")
        
        # Calculate errors (same as in tracker)
        x_error = scenario['center_x'] - target_x
        distance_error = target_distance - scenario['human_height']
        
        print(f"   X error: {x_error:+.0f}")
        print(f"   Distance error: {distance_error:+.0f}")
        
        # Simulate PID outputs (proportional only for simplicity)
        kp_speed = 0.3
        kp_turn = 0.5
        
        speed_output = kp_speed * distance_error
        turn_output = kp_turn * x_error
        
        # Apply the logic from our corrected tracker
        forward_speed = max(-100, min(100, speed_output))
        turn_speed = max(-100, min(100, turn_output * 2))
        
        # Apply deadzones
        if abs(x_error) < 30:
            turn_speed = 0
        if abs(distance_error) < 20:
            forward_speed = 0
            
        print(f"   → Forward speed: {forward_speed:+.1f}")
        print(f"   → Turn speed: {turn_speed:+.1f}")
        
        # Interpret the movement
        movements = []
        if forward_speed > 0:
            movements.append(f"FORWARD ({forward_speed:.0f})")
        elif forward_speed < 0:
            movements.append(f"BACKWARD ({abs(forward_speed):.0f})")
            
        if turn_speed > 0:
            movements.append(f"RIGHT ({turn_speed:.0f})")
        elif turn_speed < 0:
            movements.append(f"LEFT ({abs(turn_speed):.0f})")
            
        if not movements:
            movements.append("STOP")
            
        result = " + ".join(movements)
        print(f"   → Result: {result}")
        print(f"   → Expected: {scenario['expected']}")
        
        # Check if result matches expectation
        expected_lower = scenario['expected'].lower()
        result_lower = result.lower()
        
        correct = True
        if "forward" in expected_lower and "forward" not in result_lower:
            correct = False
        if "backward" in expected_lower and "backward" not in result_lower:
            correct = False
        if "right" in expected_lower and "right" not in result_lower:
            correct = False
        if "left" in expected_lower and "left" not in result_lower:
            correct = False
        if "stop" in expected_lower and "stop" not in result_lower:
            correct = False
            
        print(f"   → {'✓ CORRECT' if correct else '✗ WRONG'}")

if __name__ == "__main__":
    test_tracking_logic()