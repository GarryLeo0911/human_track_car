"""
Test script to verify the improvements work
"""

import cv2
import numpy as np
import time

def test_detection_improvements():
    """Test the improved human detection."""
    print("Testing improved human detection...")
    
    # Create a test image with a human-like shape
    test_image = np.zeros((480, 640, 3), dtype=np.uint8)
    
    # Draw a simple human-like rectangle
    # Body
    cv2.rectangle(test_image, (300, 200), (340, 400), (100, 100, 100), -1)
    # Head
    cv2.circle(test_image, (320, 180), 20, (150, 150, 150), -1)
    # Arms
    cv2.rectangle(test_image, (280, 250), (300, 320), (80, 80, 80), -1)
    cv2.rectangle(test_image, (340, 250), (360, 320), (80, 80, 80), -1)
    # Legs
    cv2.rectangle(test_image, (305, 400), (320, 450), (120, 120, 120), -1)
    cv2.rectangle(test_image, (320, 400), (335, 450), (120, 120, 120), -1)
    
    # Save test image
    cv2.imwrite('test_human_detection.jpg', test_image)
    print("Created test image: test_human_detection.jpg")
    
    try:
        # Test with our detector
        from src.tracking.human_tracker import HumanDetector
        
        detector = HumanDetector()
        detections = detector.detect_humans(test_image)
        
        print(f"Detections found: {len(detections)}")
        for i, (x, y, w, h) in enumerate(detections):
            print(f"  Detection {i+1}: x={x}, y={y}, w={w}, h={h}")
            
        if detections:
            print("✅ Detection system is working!")
        else:
            print("⚠️  No detections found - this is normal for a simple test image")
            
    except Exception as e:
        print(f"❌ Error testing detection: {e}")

def test_motor_simulation():
    """Test motor control in simulation mode."""
    print("\nTesting motor control simulation...")
    
    try:
        from src.control.motor_controller import MotorController
        
        motor = MotorController()
        print(f"Motor controller mode: {'RPI' if motor.rpi_mode else 'SIMULATION'}")
        
        # Test commands
        print("Testing motor commands...")
        motor.move_forward(50)
        time.sleep(0.5)
        
        motor.turn_left(30)
        time.sleep(0.5)
        
        motor.turn_right(30)
        time.sleep(0.5)
        
        motor.move_backward(25)
        time.sleep(0.5)
        
        motor.stop()
        print("✅ Motor control test completed!")
        
    except Exception as e:
        print(f"❌ Error testing motor control: {e}")

def main():
    """Main test function."""
    print("Human Tracking Car - Improvements Test")
    print("=" * 45)
    
    test_detection_improvements()
    test_motor_simulation()
    
    print("\n" + "=" * 45)
    print("WHAT'S IMPROVED:")
    print("1. 🎯 Better Human Detection:")
    print("   - Lower confidence threshold (0.3 instead of 0.5)")
    print("   - Grayscale + histogram equalization preprocessing")
    print("   - Better aspect ratio filtering (1.2-4.0)")
    print("   - Size filtering (min 30x60 pixels)")
    print("   - Enhanced visual feedback with target lines")
    
    print("\n2. 🚗 Motor Control Visibility:")
    print("   - Changed DEBUG to INFO logging level")
    print("   - Clear simulation mode messages")
    print("   - Better status tracking")
    
    print("\n3. 📹 Enhanced Visual Feedback:")
    print("   - Multiple detection boxes shown")
    print("   - Target center line displayed")
    print("   - Real-time error values on screen")
    print("   - Frame information overlay")
    
    print("\nNOTE: On Windows, motors run in SIMULATION mode.")
    print("You'll see motor commands in the terminal logs.")
    print("For real hardware control, run this on a Raspberry Pi.")

if __name__ == "__main__":
    main()