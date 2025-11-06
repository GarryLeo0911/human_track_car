"""
Human Detection and Tracking Module
Handles detection and tracking of humans using computer vision.
"""

import cv2
import numpy as np
import logging
from threading import Lock
from typing import Tuple, Optional, List

logger = logging.getLogger(__name__)

class HumanDetector:
    """Human detection using HOG descriptor."""
    
    def __init__(self):
        """Initialize the HOG descriptor for human detection."""
        self.hog = cv2.HOGDescriptor()
        self.hog.setSVMDetector(cv2.HOGDescriptor_getDefaultPeopleDetector())
        
    def detect_humans(self, frame: np.ndarray) -> List[Tuple[int, int, int, int]]:
        """
        Detect humans in the frame.
        
        Args:
            frame: Input frame from camera
            
        Returns:
            List of bounding boxes (x, y, w, h) for detected humans
        """
        try:
            # Resize frame for faster processing
            height, width = frame.shape[:2]
            if width > 640:
                scale = 640 / width
                new_width = 640
                new_height = int(height * scale)
                frame_resized = cv2.resize(frame, (new_width, new_height))
            else:
                frame_resized = frame.copy()
                scale = 1.0
            
            # Detect people
            boxes, weights = self.hog.detectMultiScale(
                frame_resized,
                winStride=(8, 8),
                padding=(32, 32),
                scale=1.05
            )
            
            # Scale boxes back to original size
            if scale != 1.0:
                boxes = [(int(x/scale), int(y/scale), int(w/scale), int(h/scale)) 
                        for x, y, w, h in boxes]
            
            # Filter detections by confidence
            confident_boxes = []
            for i, (x, y, w, h) in enumerate(boxes):
                if weights[i] > 0.5:  # Confidence threshold
                    confident_boxes.append((x, y, w, h))
            
            return confident_boxes
            
        except Exception as e:
            logger.error(f"Error in human detection: {e}")
            return []


class HumanTracker:
    """Main human tracking system."""
    
    def __init__(self, camera_manager, motor_controller):
        """
        Initialize the human tracker.
        
        Args:
            camera_manager: Camera management instance
            motor_controller: Motor control instance
        """
        self.camera_manager = camera_manager
        self.motor_controller = motor_controller
        self.detector = HumanDetector()
        
        # Tracking state
        self.tracking = False
        self.lock = Lock()
        self.last_human_center = None
        
        # PID controller parameters
        self.pid_x = PIDController(kp=0.5, ki=0.1, kd=0.2)
        self.pid_distance = PIDController(kp=0.3, ki=0.05, kd=0.1)
        
        # Frame dimensions (will be set when camera starts)
        self.frame_width = 640
        self.frame_height = 480
        
        # Target parameters
        self.target_x = self.frame_width // 2  # Center of frame
        self.target_distance = 150  # Target human height in pixels
        
    def start_tracking(self):
        """Start the human tracking loop."""
        logger.info("Starting human tracking...")
        self.tracking = True
        
        while self.tracking:
            try:
                # Get current frame
                frame = self.camera_manager.get_frame()
                if frame is None:
                    continue
                
                # Update frame dimensions
                self.frame_height, self.frame_width = frame.shape[:2]
                self.target_x = self.frame_width // 2
                
                # Detect humans
                human_boxes = self.detector.detect_humans(frame)
                
                if human_boxes:
                    # Select the largest detection (closest person)
                    largest_box = max(human_boxes, key=lambda box: box[2] * box[3])
                    x, y, w, h = largest_box
                    
                    # Calculate center and size
                    center_x = x + w // 2
                    center_y = y + h // 2
                    human_height = h
                    
                    # Update last known position
                    with self.lock:
                        self.last_human_center = (center_x, center_y, human_height)
                    
                    # Calculate control commands
                    self._track_human(center_x, human_height)
                    
                    # Draw detection on frame
                    cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
                    cv2.circle(frame, (center_x, center_y), 5, (0, 0, 255), -1)
                    
                else:
                    # No human detected, stop motors
                    self.motor_controller.stop()
                    with self.lock:
                        self.last_human_center = None
                
                # Update camera manager with processed frame
                self.camera_manager.set_processed_frame(frame)
                
            except Exception as e:
                logger.error(f"Error in tracking loop: {e}")
                
    def stop_tracking(self):
        """Stop the human tracking."""
        logger.info("Stopping human tracking...")
        self.tracking = False
        self.motor_controller.stop()
        
    def _track_human(self, center_x: int, human_height: int):
        """
        Control car movement to track human.
        
        Args:
            center_x: X coordinate of human center
            human_height: Height of detected human in pixels
        """
        try:
            # Calculate errors
            x_error = center_x - self.target_x
            distance_error = self.target_distance - human_height
            
            # Calculate control outputs
            turn_output = self.pid_x.update(x_error)
            speed_output = self.pid_distance.update(distance_error)
            
            # Normalize outputs
            turn_speed = max(-100, min(100, turn_output * 2))
            forward_speed = max(-100, min(100, speed_output))
            
            # Apply deadzone to prevent jittery movements
            if abs(x_error) < 30:  # X deadzone
                turn_speed = 0
            if abs(distance_error) < 20:  # Distance deadzone
                forward_speed = 0
            
            # Send commands to motor controller
            self.motor_controller.move_with_turn(forward_speed, turn_speed)
            
            logger.debug(f"Tracking: x_error={x_error}, dist_error={distance_error}, "
                        f"turn={turn_speed}, speed={forward_speed}")
                        
        except Exception as e:
            logger.error(f"Error in human tracking control: {e}")
            
    def get_tracking_status(self) -> dict:
        """Get current tracking status."""
        with self.lock:
            return {
                'tracking': self.tracking,
                'last_human_center': self.last_human_center,
                'target_center': (self.target_x, self.frame_height // 2),
                'frame_size': (self.frame_width, self.frame_height)
            }


class PIDController:
    """Simple PID controller implementation."""
    
    def __init__(self, kp: float, ki: float, kd: float):
        """
        Initialize PID controller.
        
        Args:
            kp: Proportional gain
            ki: Integral gain  
            kd: Derivative gain
        """
        self.kp = kp
        self.ki = ki
        self.kd = kd
        
        self.previous_error = 0
        self.integral = 0
        
    def update(self, error: float) -> float:
        """
        Update PID controller with new error.
        
        Args:
            error: Current error value
            
        Returns:
            Control output
        """
        # Proportional term
        p_term = self.kp * error
        
        # Integral term
        self.integral += error
        i_term = self.ki * self.integral
        
        # Derivative term
        derivative = error - self.previous_error
        d_term = self.kd * derivative
        
        # Update for next iteration
        self.previous_error = error
        
        # Calculate output
        output = p_term + i_term + d_term
        
        return output
        
    def reset(self):
        """Reset PID controller state."""
        self.previous_error = 0
        self.integral = 0