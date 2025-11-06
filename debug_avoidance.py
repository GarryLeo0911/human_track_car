#!/usr/bin/env python3
"""
Debug Tracking Logic
Test the tracking calculation logic to identify avoidance behavior.
"""

def test_tracking_calculations():
    """Test tracking calculations to understand avoidance behavior."""
    
    print("Debug: Tracking Logic Analysis")
    print("=" * 50)
    
    # Simulate scenario parameters
    target_distance = 150  # Target human height in pixels
    target_x = 320         # Center of 640px wide frame
    
    # Test scenarios where robot might avoid human
    scenarios = [
        {
            "name": "Human directly in front, correct distance",
            "human_height": 150,
            "center_x": 320,
            "expected_behavior": "STOP (perfect position)"
        },
        {
            "name": "Human too close (large in frame)",
            "human_height": 200,  # Larger = closer
            "center_x": 320,
            "expected_behavior": "MOVE BACKWARD (to increase distance)"
        },
        {
            "name": "Human too far (small in frame)",
            "human_height": 100,  # Smaller = farther
            "center_x": 320,
            "expected_behavior": "MOVE FORWARD (to decrease distance)"
        },
        {
            "name": "Human to the right",
            "human_height": 150,
            "center_x": 450,
            "expected_behavior": "TURN RIGHT (to center human)"
        },
        {
            "name": "Human to the left",
            "human_height": 150,
            "center_x": 190,
            "expected_behavior": "TURN LEFT (to center human)"
        }
    ]
    
    # Simple PID simulation
    kp_speed = 0.35
    kp_turn = 0.5
    
    print("Testing each scenario:")
    print("-" * 30)
    
    for i, scenario in enumerate(scenarios, 1):
        print(f"\n{i}. {scenario['name']}")
        print(f"   Human height: {scenario['human_height']} (target: {target_distance})")
        print(f"   Human center X: {scenario['center_x']} (target: {target_x})")
        
        # Calculate errors (current logic)
        x_error = scenario['center_x'] - target_x
        distance_error = target_distance - scenario['human_height']
        
        print(f"   X error: {x_error:+.0f} ({'RIGHT' if x_error > 0 else 'LEFT' if x_error < 0 else 'CENTERED'})")
        print(f"   Distance error: {distance_error:+.0f} ({'TOO FAR' if distance_error > 0 else 'TOO CLOSE' if distance_error < 0 else 'GOOD DISTANCE'})")
        
        # Calculate PID outputs
        speed_output = kp_speed * distance_error
        turn_output = kp_turn * x_error
        
        # Apply limits
        forward_speed = max(-100, min(100, speed_output))
        turn_speed = max(-100, min(100, turn_output))
        
        # Apply deadzones
        if abs(x_error) < 20:
            turn_speed = 0
        if abs(distance_error) < 12:
            forward_speed = 0
        
        print(f"   → PID outputs: speed_output={speed_output:+.1f}, turn_output={turn_output:+.1f}")
        print(f"   → Final commands: forward_speed={forward_speed:+.0f}, turn_speed={turn_speed:+.0f}")
        
        # Interpret movement
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
        print(f"   → Calculated behavior: {result}")
        print(f"   → Expected behavior: {scenario['expected_behavior']}")
        
        # Check if this explains avoidance behavior
        if "BACKWARD" in result and "too close" not in scenario['name'].lower():
            print(f"   ⚠ WARNING: Robot will move BACKWARD when it should move FORWARD!")
        if "FORWARD" in result and "too far" not in scenario['name'].lower():
            print(f"   ⚠ WARNING: Robot will move FORWARD when it should move BACKWARD!")
            
    print("\n" + "=" * 50)
    print("ANALYSIS:")
    print("If the robot is avoiding you, possible causes:")
    print("1. Distance calculation is inverted (larger height = farther instead of closer)")
    print("2. Motor directions are inverted (forward command moves backward)")
    print("3. PID signs are wrong (positive error causes opposite movement)")
    print("4. Target distance is wrong (robot thinks you're always too close)")

if __name__ == "__main__":
    test_tracking_calculations()