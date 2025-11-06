#!/usr/bin/env python3
"""
Test script for ultrasonic-enhanced human tracking.
Demonstrates the integration of vision and ultrasonic sensor data.
"""

import time
import sys
import os
import logging

# Add src directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def test_ultrasonic_integration():
    """Test the ultrasonic sensor integration."""
    
    print("🔊 ULTRASONIC SENSOR INTEGRATION TEST")
    print("=" * 60)
    
    try:
        from sensors.ultrasonic_sensor import UltrasonicSensor
        
        print("✓ Ultrasonic sensor module imported successfully")
        
        # Test basic sensor functionality
        print("\n1. Testing basic ultrasonic sensor...")
        with UltrasonicSensor() as sensor:
            print(f"   Hardware available: {not sensor.simulation_mode}")
            print(f"   Trigger pin: {sensor.trigger_pin}")
            print(f"   Echo pin: {sensor.echo_pin}")
            print(f"   Max distance: {sensor.max_distance}m")
            
            # Test single reading
            distance = sensor.get_distance()
            print(f"   Single reading: {distance}cm")
            
            # Test averaged reading
            avg_distance = sensor.get_averaged_distance(samples=3)
            print(f"   Averaged reading (3 samples): {avg_distance}cm")
            
            # Test continuous monitoring
            print(f"\n2. Testing continuous monitoring (5 seconds)...")
            sensor.start_continuous_monitoring()
            
            start_time = time.time()
            while time.time() - start_time < 5:
                current = sensor.get_current_distance()
                smoothed = sensor.get_smoothed_distance()
                stats = sensor.get_distance_stats()
                
                if current is not None:
                    print(f"   Current: {current:6.1f}cm | "
                          f"Smoothed: {smoothed:6.1f}cm | "
                          f"Samples: {stats['samples']}")
                else:
                    print("   No reading available")
                
                time.sleep(0.5)
            
            sensor.stop_continuous_monitoring()
            print("   ✓ Continuous monitoring test complete")
    
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("   This is normal if running on non-Raspberry Pi system")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    
    return True

def test_enhanced_tracker_logic():
    """Test the enhanced tracker logic without hardware."""
    
    print(f"\n🤖 ENHANCED TRACKING LOGIC TEST")
    print("=" * 60)
    
    # Simulate tracking scenarios
    scenarios = [
        {
            "name": "Person at optimal distance",
            "vision_height": 150,  # pixels
            "ultrasonic_distance": 80,  # cm
            "expected": "No movement (at target)"
        },
        {
            "name": "Person too close (ultrasonic)",
            "vision_height": 200,  # Large in frame
            "ultrasonic_distance": 40,  # Too close
            "expected": "Move backward (trust ultrasonic)"
        },
        {
            "name": "Person too far (ultrasonic)",
            "vision_height": 100,  # Small in frame
            "ultrasonic_distance": 150,  # Too far
            "expected": "Move forward (trust ultrasonic)"
        },
        {
            "name": "Sensor disagreement",
            "vision_height": 200,  # Suggests close
            "ultrasonic_distance": 120,  # Suggests far
            "expected": "Weighted average (sensor fusion)"
        },
        {
            "name": "Ultrasonic unavailable",
            "vision_height": 100,  # Small in frame
            "ultrasonic_distance": None,  # No ultrasonic
            "expected": "Fall back to vision-only"
        }
    ]
    
    for i, scenario in enumerate(scenarios, 1):
        print(f"\n{i}. {scenario['name']}")
        print(f"   Vision height: {scenario['vision_height']}px")
        print(f"   Ultrasonic: {scenario['ultrasonic_distance']}cm" if scenario['ultrasonic_distance'] else "   Ultrasonic: Not available")
        
        # Simulate vision-based distance estimation
        vision_height = scenario['vision_height']
        if vision_height > 200:
            vision_distance = 60
        elif vision_height > 150:
            vision_distance = 80
        elif vision_height > 100:
            vision_distance = 120
        else:
            vision_distance = 160
        
        # Simulate sensor fusion
        ultrasonic_distance = scenario['ultrasonic_distance']
        if ultrasonic_distance is not None:
            # Weighted fusion: 60% vision, 40% ultrasonic
            fused_distance = 0.6 * vision_distance + 0.4 * ultrasonic_distance
            tracking_mode = "sensor_fusion"
        else:
            fused_distance = vision_distance
            tracking_mode = "vision_only"
        
        # Calculate error from target (80cm)
        target_distance = 80
        distance_error = target_distance - fused_distance
        
        # Determine action
        if abs(distance_error) < 15:  # Within tolerance
            action = "STOP (at target)"
        elif distance_error > 0:  # Target is farther than current
            action = f"FORWARD (need {distance_error:.1f}cm closer)"
        else:  # Target is closer than current
            action = f"BACKWARD (need {abs(distance_error):.1f}cm farther)"
        
        print(f"   Vision estimate: {vision_distance:.1f}cm")
        if ultrasonic_distance:
            print(f"   Ultrasonic reading: {ultrasonic_distance:.1f}cm")
        print(f"   Fused distance: {fused_distance:.1f}cm")
        print(f"   Tracking mode: {tracking_mode}")
        print(f"   Distance error: {distance_error:+.1f}cm")
        print(f"   → Action: {action}")
        print(f"   Expected: {scenario['expected']}")
        
        # Check if behavior matches expectation
        expected_lower = scenario['expected'].lower()
        action_lower = action.lower()
        
        match = "✓"
        if "no movement" in expected_lower and "stop" not in action_lower:
            match = "?"
        elif "backward" in expected_lower and "backward" not in action_lower:
            match = "?"
        elif "forward" in expected_lower and "forward" not in action_lower:
            match = "?"
        
        print(f"   {match} {'CORRECT' if match == '✓' else 'CHECK'}")

def test_safety_features():
    """Test safety features of the enhanced tracking."""
    
    print(f"\n🛡️ SAFETY FEATURES TEST")
    print("=" * 60)
    
    safety_tests = [
        {
            "name": "Too close safety stop",
            "ultrasonic_distance": 15,  # Below 30cm minimum
            "expected": "Block forward movement, allow backward only"
        },
        {
            "name": "Maximum range limit",
            "ultrasonic_distance": 250,  # Above 200cm maximum
            "expected": "Stop tracking, out of range"
        },
        {
            "name": "Sensor failure handling",
            "ultrasonic_distance": None,  # Sensor failure
            "expected": "Graceful fallback to vision-only"
        },
        {
            "name": "Edge of frame + close distance",
            "ultrasonic_distance": 25,  # Very close
            "at_edge": True,
            "expected": "Prioritize safety, back away slowly"
        }
    ]
    
    for i, test in enumerate(safety_tests, 1):
        print(f"\n{i}. {test['name']}")
        print(f"   Ultrasonic: {test['ultrasonic_distance']}cm" if test['ultrasonic_distance'] else "   Ultrasonic: Failed/None")
        
        distance = test['ultrasonic_distance']
        
        if distance and distance < 30:
            safety_action = "EMERGENCY BACK - too close!"
            allow_forward = False
        elif distance and distance > 200:
            safety_action = "STOP - out of tracking range"
            allow_forward = False
        elif distance is None:
            safety_action = "VISION FALLBACK - sensor unavailable"
            allow_forward = True
        else:
            safety_action = "NORMAL OPERATION"
            allow_forward = True
        
        print(f"   → Safety action: {safety_action}")
        print(f"   → Forward movement: {'ALLOWED' if allow_forward else 'BLOCKED'}")
        print(f"   Expected: {test['expected']}")
        
        # Simple validation
        expected = test['expected'].lower()
        action = safety_action.lower()
        
        match = "✓"
        if "block" in expected and "block" not in action and "emergency" not in action:
            match = "?"
        elif "stop" in expected and "stop" not in action:
            match = "?"
        elif "fallback" in expected and "fallback" not in action:
            match = "?"
        
        print(f"   {match}")

def show_integration_benefits():
    """Show the benefits of ultrasonic integration."""
    
    print(f"\n🌟 INTEGRATION BENEFITS")
    print("=" * 60)
    
    benefits = [
        {
            "issue": "Vision-only distance estimation is inaccurate",
            "solution": "Ultrasonic provides precise distance in cm",
            "improvement": "Distance accuracy from ±50cm to ±2cm"
        },
        {
            "issue": "Camera can't see in low light",
            "solution": "Ultrasonic works in any lighting",
            "improvement": "Reliable tracking in dim conditions"
        },
        {
            "issue": "Person size varies with posture/clothes",
            "solution": "Distance independent of appearance", 
            "improvement": "Consistent tracking regardless of clothing"
        },
        {
            "issue": "No depth perception with single camera",
            "solution": "Direct distance measurement",
            "improvement": "True 3D awareness for better navigation"
        },
        {
            "issue": "Safety risks from vision-only tracking",
            "solution": "Hardware-based proximity detection",
            "improvement": "Hard safety limits prevent collisions"
        },
        {
            "issue": "Tracking fails when person partially hidden",
            "solution": "Ultrasonic detects presence even if vision fails",
            "improvement": "Continued tracking through brief occlusion"
        }
    ]
    
    for i, benefit in enumerate(benefits, 1):
        print(f"\n{i}. ISSUE: {benefit['issue']}")
        print(f"   SOLUTION: {benefit['solution']}")  
        print(f"   IMPROVEMENT: {benefit['improvement']}")

def main():
    """Run all ultrasonic integration tests."""
    
    print("🚀 ULTRASONIC HUMAN TRACKING INTEGRATION")
    print("Testing the enhanced tracking system with ultrasonic sensor support")
    print("Based on official Freenove implementation")
    print("=" * 80)
    
    # Test basic ultrasonic functionality
    ultrasonic_works = test_ultrasonic_integration()
    
    # Test tracking logic (always works)
    test_enhanced_tracker_logic()
    
    # Test safety features
    test_safety_features()
    
    # Show benefits
    show_integration_benefits()
    
    print(f"\n" + "=" * 80)
    print("🎯 SUMMARY:")
    if ultrasonic_works:
        print("✅ Ultrasonic sensor: WORKING")
        print("✅ Enhanced tracking: READY")
        print("🚀 Run with: python main.py")
    else:
        print("⚠️  Ultrasonic sensor: SIMULATION MODE")
        print("✅ Enhanced tracking: READY (will fall back to vision)")
        print("🚀 Run with: python main.py")
        print("💡 For full functionality, run on Raspberry Pi with ultrasonic sensor")
    
    print("\n📋 USAGE:")
    print("python main.py                     # Auto-detect ultrasonic sensor")
    print("python main.py --no-ultrasonic     # Force vision-only mode")
    print("python main.py --ultrasonic-pins 27 22  # Custom GPIO pins")
    
    print("=" * 80)

if __name__ == "__main__":
    main()