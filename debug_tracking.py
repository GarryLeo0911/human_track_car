#!/usr/bin/env python3
"""
Debug version of human tracking with enhanced logging.
Run this to see exactly what the car is trying to do.
"""

import time
import cv2
import logging
import sys
import os

# Add src directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.tracking.human_tracker import HumanTracker, HumanDetector
from src.camera.camera_manager import CameraManager  
from src.control.freenove_motor_controller import FreenoveMotorController

# Configure detailed logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def debug_tracking():
    """Run tracking with enhanced debug output."""
    
    print("Starting DEBUG Human Tracking")
    print("Watch the terminal output to see what decisions the car is making")
    print("=" * 60)
    
    # Initialize components
    camera = CameraManager()
    motor = FreenoveMotorController()
    tracker = HumanTracker(camera, motor)
    
    print(f"Target distance (human height): {tracker.target_distance} pixels")
    print(f"Frame center X: {tracker.target_x}")
    print("Press 'q' to quit")
    print("")
    
    try:
        # Camera starts automatically when initialized
        
        # Manual tracking loop with detailed output
        detector = HumanDetector()
        
        while True:
            frame = camera.get_frame()
            if frame is None:
                continue
                
            # Update frame dimensions
            tracker.frame_height, tracker.frame_width = frame.shape[:2]
            tracker.target_x = tracker.frame_width // 2
            
            # Detect humans
            human_boxes = detector.detect_humans(frame)
            
            if human_boxes:
                # Get largest detection
                largest_box = max(human_boxes, key=lambda box: box[2] * box[3])
                x, y, w, h = largest_box
                
                center_x = x + w // 2
                center_y = y + h // 2
                human_height = h
                
                # Calculate errors
                x_error = center_x - tracker.target_x
                distance_error = tracker.target_distance - human_height
                
                # Show what the car is thinking
                print(f"\n--- TRACKING DECISION ---")
                print(f"Human detected: {w}x{h} at ({center_x}, {center_y})")
                print(f"Target center: {tracker.target_x}, Target height: {tracker.target_distance}")
                print(f"X Error: {x_error:+.0f} ({'LEFT' if x_error < 0 else 'RIGHT' if x_error > 0 else 'CENTERED'})")
                print(f"Distance Error: {distance_error:+.0f} ({'TOO CLOSE' if distance_error < 0 else 'TOO FAR' if distance_error > 0 else 'GOOD DISTANCE'})")
                
                # Calculate what the PID would do
                turn_output = tracker.pid_x.update(x_error)
                speed_output = tracker.pid_distance.update(distance_error)
                
                forward_speed = max(-100, min(100, speed_output))
                turn_speed = max(-100, min(100, turn_output * 2))
                
                # Apply deadzone
                if abs(x_error) < 30:
                    turn_speed = 0
                if abs(distance_error) < 20:
                    forward_speed = 0
                    
                print(f"PID Outputs: speed_output={speed_output:+.1f}, turn_output={turn_output:+.1f}")
                print(f"Final Commands: forward_speed={forward_speed:+.0f}, turn_speed={turn_speed:+.0f}")
                
                if forward_speed > 0:
                    print(f"→ MOVING FORWARD (speed={forward_speed})")
                elif forward_speed < 0:
                    print(f"→ MOVING BACKWARD (speed={abs(forward_speed)})")
                else:
                    print(f"→ NOT MOVING (in distance deadzone)")
                    
                if turn_speed > 0:
                    print(f"→ TURNING RIGHT (speed={turn_speed})")
                elif turn_speed < 0:
                    print(f"→ TURNING LEFT (speed={abs(turn_speed)})")
                else:
                    print(f"→ NOT TURNING (in turn deadzone)")
                
                # Send command
                motor.move_with_turn(forward_speed, turn_speed)
                
                # Draw on frame
                cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
                cv2.circle(frame, (center_x, center_y), 8, (0, 0, 255), -1)
                cv2.line(frame, (tracker.target_x, 0), (tracker.target_x, tracker.frame_height), (255, 0, 0), 2)
                
                # Status text
                cv2.putText(frame, f"Height: {human_height} (target: {tracker.target_distance})", 
                           (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
                cv2.putText(frame, f"X: {center_x} (target: {tracker.target_x})", 
                           (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
                cv2.putText(frame, f"Forward: {forward_speed:+.0f}", 
                           (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
                cv2.putText(frame, f"Turn: {turn_speed:+.0f}", 
                           (10, 120), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
                
            else:
                print("No human detected - stopping motors")
                motor.stop()
                cv2.putText(frame, "Searching for humans...", (10, 30), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
            
            # Display frame
            cv2.imshow('Debug Human Tracking', frame)
            
            # Check for quit
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
                
    except KeyboardInterrupt:
        print("\nTracking stopped by user")
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        motor.stop()
        motor.cleanup()
        camera.cleanup()
        cv2.destroyAllWindows()
        print("Debug tracking ended")

if __name__ == "__main__":
    debug_tracking()