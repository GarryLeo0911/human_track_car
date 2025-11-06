#!/usr/bin/env python3
"""
Enhanced Tracking Demo Script
Demonstrates the improved tracking capabilities learned from target_follow project
"""

import cv2
import time
import logging
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.tracking.ultra_light_tracker import UltraLightHumanTracker
from src.control.freenove_motor_controller import FreenoveMotorController

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MockMotorController:
    """Mock motor controller for testing"""
    
    def __init__(self):
        self.current_speed = 0
        self.current_turn = 0
        
    def move_with_turn(self, speed, turn):
        self.current_speed = speed
        self.current_turn = turn
        print(f"Motor Command: Speed={speed:.2f}, Turn={turn:.2f}")
    
    def stop(self):
        self.current_speed = 0
        self.current_turn = 0
        print("Motor: STOP")

class MockCameraManager:
    """Mock camera manager for testing"""
    
    def __init__(self):
        self.cap = cv2.VideoCapture(0)
        if self.cap.isOpened():
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    
    def get_frame(self):
        if self.cap.isOpened():
            ret, frame = self.cap.read()
            return ret, frame
        return False, None
    
    def release(self):
        if self.cap.isOpened():
            self.cap.release()

def demo_enhanced_tracking():
    """Demo enhanced tracking with different detectors"""
    print("Enhanced Human Tracking Demo")
    print("===========================")
    print("Based on learnings from ro-ken/target_follow project")
    print()
    print("Key improvements:")
    print("- Distance estimation based on target size")
    print("- Multi-target selection with tracking continuity")
    print("- Smooth acceleration/deceleration control")
    print("- Better turning logic with proportional control")
    print("- Safety distance maintenance")
    print()
    
    # Initialize components
    motor_controller = MockMotorController()
    camera_manager = MockCameraManager()
    
    # Test different detector types
    detector_types = [
        ('enhanced_motion', 'Enhanced Motion Detection'),
        ('enhanced_edge', 'Enhanced Edge Detection'), 
        ('hybrid', 'Hybrid Detection (Best)')
    ]
    
    current_detector_idx = 0
    detector_type, detector_name = detector_types[current_detector_idx]
    
    # Initialize tracker with enhanced control
    tracker = UltraLightHumanTracker(
        camera_manager=camera_manager,
        motor_controller=motor_controller,
        detector_type=detector_type
    )
    
    # Enable enhanced control (this is the new feature)
    tracker.enable_enhanced_control(True)
    
    print(f"Starting with: {detector_name}")
    print("Controls:")
    print("- 'c': Cycle through detectors")
    print("- 't': Toggle enhanced/legacy tracking")
    print("- 'r': Reset tracking")
    print("- 'q': Quit")
    print()
    
    # Start tracking
    tracker.start_tracking()
    
    enhanced_mode = True
    
    try:
        while True:
            ret, frame = camera_manager.get_frame()
            if not ret:
                print("Cannot read camera frame")
                break
            
            # The tracker automatically processes the frame and controls the robot
            # No manual processing needed in main loop
            
            # Get tracking status for display
            status = tracker.get_tracking_status()
            
            # Display tracking info
            if enhanced_mode and 'enhanced_info' in status:
                enhanced_info = status['enhanced_info']
                info_text = (
                    f"Mode: Enhanced | Detector: {detector_name}\n"
                    f"Speed: {enhanced_info['current_speed']:.2f} | "
                    f"Turn: {enhanced_info['current_turn']:.2f}\n"
                    f"Distance: {enhanced_info['distance_estimate']:.1f}m | "
                    f"Lost frames: {enhanced_info['target_lost_count']}"
                )
            else:
                info_text = f"Mode: Legacy | Detector: {detector_name}"
            
            # Draw info on frame
            y_offset = 130
            for i, line in enumerate(info_text.split('\n')):
                cv2.putText(frame, line, (10, y_offset + i * 20), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 0), 1)
            
            # Draw controls help
            cv2.putText(frame, "Press 'c' cycle, 't' toggle mode, 'r' reset, 'q' quit", 
                       (10, frame.shape[0] - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
            
            cv2.imshow('Enhanced Human Tracking Demo', frame)
            
            # Handle key press
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                break
            elif key == ord('c'):
                # Cycle to next detector
                tracker.stop_tracking()
                current_detector_idx = (current_detector_idx + 1) % len(detector_types)
                detector_type, detector_name = detector_types[current_detector_idx]
                
                # Create new tracker with different detector
                tracker = UltraLightHumanTracker(
                    camera_manager=camera_manager,
                    motor_controller=motor_controller,
                    detector_type=detector_type
                )
                tracker.enable_enhanced_control(enhanced_mode)
                tracker.start_tracking()
                print(f"Switched to: {detector_name}")
                
            elif key == ord('t'):
                # Toggle enhanced/legacy mode
                enhanced_mode = not enhanced_mode
                tracker.enable_enhanced_control(enhanced_mode)
                mode_text = "Enhanced" if enhanced_mode else "Legacy"
                print(f"Switched to {mode_text} tracking mode")
                
            elif key == ord('r'):
                # Reset tracking
                if enhanced_mode:
                    tracker.enhanced_controller.reset_tracking()
                print("Tracking reset")
            
            time.sleep(0.01)  # Small delay to prevent high CPU usage
    
    finally:
        tracker.stop_tracking()
        camera_manager.release()
        cv2.destroyAllWindows()
        print("Demo completed!")

def performance_comparison():
    """Compare performance between enhanced and legacy tracking"""
    print("\nPerformance Comparison Demo")
    print("===========================")
    
    motor_controller = MockMotorController()
    camera_manager = MockCameraManager()
    
    # Test with hybrid detector (most advanced)
    tracker = UltraLightHumanTracker(
        camera_manager=camera_manager,
        motor_controller=motor_controller,
        detector_type='hybrid'
    )
    
    print("Testing Legacy vs Enhanced tracking performance...")
    
    modes = [
        (False, "Legacy Tracking"),
        (True, "Enhanced Tracking")
    ]
    
    for enhanced_mode, mode_name in modes:
        print(f"\nTesting {mode_name}...")
        
        tracker.enable_enhanced_control(enhanced_mode)
        tracker.start_tracking()
        
        detection_times = []
        control_responses = []
        
        # Test for 5 seconds
        start_time = time.time()
        frame_count = 0
        
        while time.time() - start_time < 5.0:
            ret, frame = camera_manager.get_frame()
            if not ret:
                break
                
            frame_start = time.time()
            
            # Get tracking status to measure response time
            status = tracker.get_tracking_status()
            
            frame_time = (time.time() - frame_start) * 1000
            detection_times.append(frame_time)
            
            frame_count += 1
            
            if frame_count % 30 == 0:  # Print every second (assuming 30 FPS)
                print(f"  Processed {frame_count} frames, avg time: {sum(detection_times)/len(detection_times):.1f}ms")
        
        tracker.stop_tracking()
        
        # Print results
        avg_time = sum(detection_times) / len(detection_times) if detection_times else 0
        print(f"  {mode_name} Results:")
        print(f"    Average processing time: {avg_time:.1f}ms")
        print(f"    Total frames processed: {frame_count}")
        print(f"    FPS: {frame_count / 5.0:.1f}")
    
    camera_manager.release()
    print("\nPerformance comparison completed!")

def main():
    """Main demo function"""
    print("Enhanced Human Tracking System Demo")
    print("Based on target_follow project improvements")
    print("==========================================")
    
    while True:
        print("\nChoose demo mode:")
        print("1. Interactive enhanced tracking demo")
        print("2. Performance comparison (legacy vs enhanced)")
        print("3. Exit")
        
        choice = input("Enter choice (1-3): ").strip()
        
        if choice == '1':
            demo_enhanced_tracking()
        elif choice == '2':
            performance_comparison()
        elif choice == '3':
            break
        else:
            print("Invalid choice")
    
    print("Demo finished!")

if __name__ == "__main__":
    main()