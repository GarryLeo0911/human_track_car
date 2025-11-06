#!/usr/bin/env python3
"""
Test script for step-by-step turning functionality.
This script demonstrates the new stepped turning behavior.
"""

import time
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def simulate_step_turning():
    """Simulate the step-by-step turning behavior."""
    
    print("🚗 Step-by-Step Turning Test")
    print("=" * 50)
    print()
    
    # Simulate turn step parameters
    turn_step_duration = 0.3  # Seconds per step
    turn_pause_duration = 0.2  # Pause between steps
    max_turn_speed = 25
    step_speed_factor = 0.4
    
    # Simulate tracking state
    is_in_turn_step = False
    current_turn_direction = 0
    last_turn_step_time = 0
    
    # Simulate human positions (x_error values)
    scenarios = [
        ("Human far left", -150),
        ("Human slightly left", -80),
        ("Human centered", -10),
        ("Human slightly right", 70),
        ("Human far right", 120)
    ]
    
    for scenario_name, x_error in scenarios:
        print(f"\n📍 Scenario: {scenario_name} (x_error = {x_error})")
        print("-" * 40)
        
        # Reset state for each scenario
        is_in_turn_step = False
        current_turn_direction = 0
        last_turn_step_time = time.time()
        
        # Simulate 10 tracking cycles (about 3 seconds)
        for cycle in range(10):
            current_time = time.time()
            
            # Determine desired turn direction
            if x_error > 60:
                desired_direction = 1  # Right
                desired_speed = max_turn_speed * step_speed_factor
            elif x_error < -60:
                desired_direction = -1  # Left
                desired_speed = max_turn_speed * step_speed_factor
            else:
                desired_direction = 0  # Centered
                desired_speed = 0
            
            # Apply step turning logic
            actual_turn_speed = 0
            
            if desired_direction != 0:  # Need to turn
                if is_in_turn_step:
                    # Currently turning
                    if current_time - last_turn_step_time >= turn_step_duration:
                        # End turn step, start pause
                        is_in_turn_step = False
                        last_turn_step_time = current_time
                        actual_turn_speed = 0
                        status = "🛑 Step complete, starting pause"
                    else:
                        # Continue turning
                        actual_turn_speed = current_turn_direction * desired_speed
                        status = f"🔄 Turning {current_turn_direction * desired_speed:+.1f}"
                        
                elif current_turn_direction != 0:
                    # In pause between steps
                    if current_time - last_turn_step_time >= turn_pause_duration:
                        # Start new turn step
                        current_turn_direction = desired_direction
                        is_in_turn_step = True
                        last_turn_step_time = current_time
                        actual_turn_speed = current_turn_direction * desired_speed
                        status = f"▶️  Starting new step {actual_turn_speed:+.1f}"
                    else:
                        # Still pausing
                        actual_turn_speed = 0
                        status = "⏸️  Pausing between steps"
                        
                else:
                    # Start first turn step
                    current_turn_direction = desired_direction
                    is_in_turn_step = True
                    last_turn_step_time = current_time
                    actual_turn_speed = current_turn_direction * desired_speed
                    status = f"🚀 Starting first step {actual_turn_speed:+.1f}"
            else:
                # No turning needed
                current_turn_direction = 0
                is_in_turn_step = False
                actual_turn_speed = 0
                status = "✅ Centered - no turning needed"
            
            print(f"  Cycle {cycle+1:2d}: {status}")
            
            # Simulate frame processing time
            time.sleep(0.3)
            
            # Break early if centered
            if desired_direction == 0:
                break
    
    print()
    print("🎯 Step-by-Step Turning Benefits:")
    print("   • Ultra-smooth movement with discrete steps")
    print("   • Pause between steps allows reassessment") 
    print("   • Prevents oscillation and radical movements")
    print("   • More human-like, deliberate tracking behavior")
    print()

if __name__ == "__main__":
    simulate_step_turning()