#!/usr/bin/env python3
"""
Test the improved tracking stability and edge handling.
"""

def test_improved_tracking():
    """Simulate the improved tracking scenarios."""
    
    print("Testing Improved Human Tracking")
    print("=" * 50)
    
    # Simulation parameters
    frame_width = 640
    target_x = frame_width // 2  # 320
    edge_threshold = 100
    max_turn_speed = 60  # Reduced from 100
    
    scenarios = [
        {
            "name": "Human at LEFT EDGE (high overshoot risk)",
            "center_x": 50,    # Very close to left edge
            "expected_behavior": "Gentle right turn (reduced response)"
        },
        {
            "name": "Human at RIGHT EDGE (high overshoot risk)", 
            "center_x": 590,   # Very close to right edge
            "expected_behavior": "Gentle left turn (reduced response)"
        },
        {
            "name": "Human far left but not at edge",
            "center_x": 150,   # Left but not at edge
            "expected_behavior": "Normal right turn"
        },
        {
            "name": "Human far right but not at edge",
            "center_x": 490,   # Right but not at edge  
            "expected_behavior": "Normal left turn"
        },
        {
            "name": "Human slightly off center",
            "center_x": 350,   # Just 30 pixels off center
            "expected_behavior": "No movement (in deadzone)"
        }
    ]
    
    for i, scenario in enumerate(scenarios, 1):
        print(f"\n{i}. {scenario['name']}")
        print(f"   Position: X={scenario['center_x']} (center={target_x})")
        
        # Calculate x_error
        x_error = scenario['center_x'] - target_x
        
        # Check if at edge
        is_at_left_edge = scenario['center_x'] < edge_threshold
        is_at_right_edge = scenario['center_x'] > (frame_width - edge_threshold)
        is_at_edge = is_at_left_edge or is_at_right_edge
        
        print(f"   X Error: {x_error:+.0f}")
        print(f"   At Edge: {'YES' if is_at_edge else 'NO'}")
        
        # Simulate PID output (proportional only)
        kp_turn = 0.3  # Reduced gain
        turn_output = kp_turn * x_error
        
        # Apply adaptive scaling
        if is_at_edge:
            turn_scale = 0.5  # Much gentler when at edge
            print(f"   → EDGE DETECTED: Applying 50% scale reduction")
        elif abs(x_error) > 150:
            turn_scale = 0.7   # Moderate response for large errors
            print(f"   → LARGE ERROR: Applying 30% scale reduction")
        else:
            turn_scale = 1.0
            print(f"   → NORMAL: No scale reduction")
        
        # Calculate turn speed
        turn_speed = max(-max_turn_speed, min(max_turn_speed, turn_output * turn_scale))
        
        # Apply enhanced deadzone
        x_deadzone = 50 if is_at_edge else 30
        if abs(x_error) < x_deadzone:
            turn_speed = 0
            print(f"   → IN DEADZONE ({x_deadzone}px): No movement")
        
        print(f"   → Turn Speed: {turn_speed:+.1f} (max: ±{max_turn_speed})")
        
        # Interpret result
        if turn_speed > 0:
            result = f"Turn RIGHT ({turn_speed:.0f})"
        elif turn_speed < 0:
            result = f"Turn LEFT ({abs(turn_speed):.0f})"
        else:
            result = "NO MOVEMENT"
            
        print(f"   → Result: {result}")
        print(f"   → Expected: {scenario['expected_behavior']}")
        
        # Improvement indicators
        improvements = []
        if is_at_edge and abs(turn_speed) < 30:
            improvements.append("✓ Gentle edge response")
        if abs(x_error) < x_deadzone and turn_speed == 0:
            improvements.append("✓ Deadzone prevents jitter")
        if turn_scale < 1.0:
            improvements.append("✓ Adaptive scaling reduces overshoot")
            
        if improvements:
            print(f"   → Improvements: {', '.join(improvements)}")

    print(f"\n" + "=" * 50)
    print("KEY IMPROVEMENTS:")
    print("• Reduced PID gains (0.3 vs 0.5) for stability")
    print("• Adaptive scaling: 50% reduction at edges")
    print("• Enhanced deadzones: 50px at edges vs 30px normal")
    print("• Movement smoothing over 3 frames")
    print("• Intelligent search when human disappears")
    print("• Maximum turn speed limited to 60 (vs 100)")

if __name__ == "__main__":
    test_improved_tracking()