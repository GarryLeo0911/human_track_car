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
        # Use numpy array for the detector
        import numpy as np
        detector = cv2.HOGDescriptor.getDefaultPeopleDetector()
        self.hog.setSVMDetector(np.array(detector, dtype=np.float32))
        
    def detect_humans(self, frame: np.ndarray) -> List[Tuple[int, int, int, int]]:
        """
        Detect humans in the frame.
        
        Args:
            frame: Input frame from camera
            
        Returns:
            List of bounding boxes (x, y, w, h) for detected humans
        """
        try:
            # Preprocess frame for better detection
            height, width = frame.shape[:2]
            
            # Convert to grayscale for HOG (more stable)
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            
            # Enhance contrast for better detection
            gray = cv2.equalizeHist(gray)
            
            # Resize frame for processing (keep original aspect ratio)
            if width > 480:
                scale = 480 / width
                new_width = 480
                new_height = int(height * scale)
                gray_resized = cv2.resize(gray, (new_width, new_height))
            else:
                gray_resized = gray.copy()
                scale = 1.0
            
            # Detect people with improved parameters
            boxes, weights = self.hog.detectMultiScale(
                gray_resized,
                winStride=(4, 4),        # Smaller stride for better detection
                padding=(16, 16),        # Smaller padding  
                scale=1.02               # Smaller scale step for more thorough search
            )
            
            # Scale boxes back to original size
            if scale != 1.0:
                boxes = [(int(x/scale), int(y/scale), int(w/scale), int(h/scale)) 
                        for x, y, w, h in boxes]
            
            # Filter detections
            confident_boxes = []
            for i, (x, y, w, h) in enumerate(boxes):
                # Lower confidence threshold and add size filtering
                if weights[i] > 0.3:  # Lower confidence threshold
                    # Filter by reasonable human dimensions
                    aspect_ratio = h / w if w > 0 else 0
                    if 1.2 < aspect_ratio < 4.0 and w > 30 and h > 60:  # Reasonable human proportions
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
        
        # PID controller parameters - REDUCED for stability
        self.pid_x = PIDController(kp=0.3, ki=0.02, kd=0.15)      # Reduced from 0.5, 0.1, 0.2
        self.pid_distance = PIDController(kp=0.2, ki=0.01, kd=0.08)  # Reduced from 0.3, 0.05, 0.1
        
        # Frame dimensions (will be set when camera starts)
        self.frame_width = 640
        self.frame_height = 480
        
        # Target parameters
        self.target_x = self.frame_width // 2  # Center of frame
        self.target_distance = 150  # Target human height in pixels
        
        # Adaptive control parameters
        self.max_turn_speed = 60      # Reduced from 100 to prevent overshooting
        self.max_forward_speed = 80   # Reduced from 100 for smoother movement
        
        # Edge detection and compensation
        self.edge_threshold = 100     # Pixels from edge to be considered "at edge"
        self.last_valid_center = None
        self.frames_since_detection = 0
        self.max_frames_without_detection = 10  # Stop after this many frames
        
        # Movement smoothing
        self.movement_history = []
        self.history_length = 3       # Average over last 3 movements
        
    def start_tracking(self):
        """Start the human tracking loop."""
        logger.info("Starting human tracking...")
        self.tracking = True
        
        # Reset PID controllers to prevent accumulated error
        self.pid_x.reset()
        self.pid_distance.reset()
        self.movement_history.clear()
        self.frames_since_detection = 0
        self.last_valid_center = None
        
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
                    
                    # Draw detection on frame with enhanced visualization
                    # Main bounding box
                    cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
                    
                    # Center point
                    cv2.circle(frame, (center_x, center_y), 8, (0, 0, 255), -1)
                    cv2.circle(frame, (center_x, center_y), 12, (255, 255, 255), 2)
                    
                    # Target center line
                    cv2.line(frame, (self.target_x, 0), (self.target_x, self.frame_height), (255, 0, 0), 2)
                    
                    # Distance and error info
                    x_error = center_x - self.target_x
                    distance_error = self.target_distance - human_height
                    
                    # Status text
                    cv2.putText(frame, f"Target Found", (10, 30), 
                               cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
                    cv2.putText(frame, f"Center: ({center_x}, {center_y})", (10, 60), 
                               cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
                    cv2.putText(frame, f"Size: {w}x{h}", (10, 90), 
                               cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
                    cv2.putText(frame, f"X Error: {x_error}", (10, 120), 
                               cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)
                    cv2.putText(frame, f"Dist Error: {distance_error}", (10, 150), 
                               cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)
                    
                    # Add movement direction indicators
                    cv2.putText(frame, f"Target Height: {self.target_distance}", (10, 180), 
                               cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
                    if human_height > self.target_distance:
                        cv2.putText(frame, "TOO CLOSE - BACKING UP", (10, 210), 
                                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
                    elif human_height < self.target_distance:
                        cv2.putText(frame, "TOO FAR - MOVING FORWARD", (10, 210), 
                                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
                    else:
                        cv2.putText(frame, "DISTANCE OK", (10, 210), 
                                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)
                    
                    # Add edge detection indicators
                    is_at_left_edge = center_x < self.edge_threshold
                    is_at_right_edge = center_x > (self.frame_width - self.edge_threshold)
                    is_at_edge = is_at_left_edge or is_at_right_edge
                    
                    edge_color = (0, 165, 255) if is_at_edge else (255, 255, 255)
                    edge_text = "AT EDGE!" if is_at_edge else "CENTERED"
                    cv2.putText(frame, edge_text, (10, 240), 
                               cv2.FONT_HERSHEY_SIMPLEX, 0.6, edge_color, 2)
                    
                    # Draw edge zones
                    if is_at_left_edge:
                        cv2.rectangle(frame, (0, 0), (self.edge_threshold, self.frame_height), (0, 165, 255), 2)
                    if is_at_right_edge:
                        cv2.rectangle(frame, (self.frame_width - self.edge_threshold, 0), 
                                     (self.frame_width, self.frame_height), (0, 165, 255), 2)
                    
                    # Draw all detections (not just the largest)
                    for i, (hx, hy, hw, hh) in enumerate(human_boxes):
                        if (hx, hy, hw, hh) != largest_box:
                            cv2.rectangle(frame, (hx, hy), (hx + hw, hy + hh), (0, 255, 255), 1)
                            cv2.putText(frame, f"#{i+1}", (hx, hy-10), 
                                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1)
                    
                else:
                    # No human detected - use improved search behavior
                    self._handle_no_detection()
                    with self.lock:
                        self.last_human_center = None
                    
                    # Draw "searching" indicator with more info
                    cv2.putText(frame, f"Searching... ({self.frames_since_detection}/{self.max_frames_without_detection})", 
                               (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
                    if self.last_valid_center is not None:
                        cv2.putText(frame, f"Last seen at X: {self.last_valid_center}", (10, 60), 
                                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)
                    cv2.line(frame, (self.target_x, 0), (self.target_x, self.frame_height), (128, 128, 128), 1)
                
                # Draw frame info
                cv2.putText(frame, f"Frame: {self.frame_width}x{self.frame_height}", 
                           (self.frame_width-200, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
                cv2.putText(frame, f"Target X: {self.target_x}", 
                           (self.frame_width-200, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
                
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
        Control car movement to track human with improved stability.
        
        Args:
            center_x: X coordinate of human center
            human_height: Height of detected human in pixels
        """
        try:
            # Reset frames counter since we have detection
            self.frames_since_detection = 0
            self.last_valid_center = center_x
            
            # Calculate errors
            x_error = center_x - self.target_x
            distance_error = self.target_distance - human_height
            
            # Detect if human is at edge of frame
            is_at_left_edge = center_x < self.edge_threshold
            is_at_right_edge = center_x > (self.frame_width - self.edge_threshold)
            is_at_edge = is_at_left_edge or is_at_right_edge
            
            # Calculate control outputs
            turn_output = self.pid_x.update(x_error)
            speed_output = self.pid_distance.update(distance_error)
            
            # Apply adaptive scaling based on error magnitude and edge detection
            if is_at_edge:
                # Reduce turn response when at edge to prevent overshoot
                turn_scale = 0.5  # Much gentler when at edge
                speed_scale = 0.7  # Also reduce forward speed when turning
                logger.info(f"EDGE DETECTION: Human at edge, reducing response")
            elif abs(x_error) > 150:  # Large error (far from center)
                turn_scale = 0.7   # Moderate response for large errors
                speed_scale = 0.8
            else:  # Normal operation
                turn_scale = 1.0
                speed_scale = 1.0
            
            # Calculate speeds with scaling
            forward_speed = max(-self.max_forward_speed, min(self.max_forward_speed, speed_output * speed_scale))
            turn_speed = max(-self.max_turn_speed, min(self.max_turn_speed, turn_output * turn_scale))
            
            # Enhanced deadzones - larger when at edge
            x_deadzone = 50 if is_at_edge else 30      # Larger deadzone at edge
            distance_deadzone = 25 if is_at_edge else 20
            
            if abs(x_error) < x_deadzone:
                turn_speed = 0
            if abs(distance_error) < distance_deadzone:
                forward_speed = 0
            
            # Movement smoothing - average with recent movements
            current_movement = (forward_speed, turn_speed)
            self.movement_history.append(current_movement)
            if len(self.movement_history) > self.history_length:
                self.movement_history.pop(0)
            
            # Calculate smoothed movement
            if len(self.movement_history) > 1:
                avg_forward = sum(m[0] for m in self.movement_history) / len(self.movement_history)
                avg_turn = sum(m[1] for m in self.movement_history) / len(self.movement_history)
                
                # Blend current with average (more smoothing at edges)
                smooth_factor = 0.7 if is_at_edge else 0.3
                forward_speed = smooth_factor * avg_forward + (1 - smooth_factor) * forward_speed
                turn_speed = smooth_factor * avg_turn + (1 - smooth_factor) * turn_speed
            
            # Send commands to motor controller
            self.motor_controller.move_with_turn(forward_speed, turn_speed)
            
            # Enhanced logging
            edge_status = "EDGE" if is_at_edge else "CENTER"
            logger.info(f"TRACKING [{edge_status}]: x_error={x_error:+4.0f}, dist_error={distance_error:+4.0f}, "
                       f"turn={turn_speed:+4.1f}, speed={forward_speed:+4.1f}, scale=({turn_scale:.1f},{speed_scale:.1f})")
                        
        except Exception as e:
            logger.error(f"Error in human tracking control: {e}")
            
    def _handle_no_detection(self):
        """Handle case when no human is detected."""
        self.frames_since_detection += 1
        
        if self.frames_since_detection <= self.max_frames_without_detection:
            # Try to recover by using last known position
            if self.last_valid_center is not None:
                # Determine which direction to search based on last position
                if self.last_valid_center < self.target_x - 50:
                    # Human was on left, turn left gently to find them
                    self.motor_controller.move_with_turn(0, -20)
                    logger.info("SEARCHING: Gentle left turn to find human")
                elif self.last_valid_center > self.target_x + 50:
                    # Human was on right, turn right gently to find them
                    self.motor_controller.move_with_turn(0, 20)
                    logger.info("SEARCHING: Gentle right turn to find human")
                else:
                    # Human was center, stop and wait
                    self.motor_controller.stop()
                    logger.info("SEARCHING: Waiting at center")
            else:
                # No previous position, stop
                self.motor_controller.stop()
        else:
            # Been too long without detection, stop completely
            self.motor_controller.stop()
            self.movement_history.clear()  # Reset movement history
            logger.info("LOST: No human detected for too long, stopping")
            
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