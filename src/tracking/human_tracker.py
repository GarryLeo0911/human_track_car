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
            
            # SPEED OPTIMIZATION: Skip contrast enhancement for faster processing
            # gray = cv2.equalizeHist(gray)  # Commented out for speed
            
            # SPEED OPTIMIZATION: More aggressive resizing for faster detection
            if width > 320:  # Reduced from 480 to 320 for speed
                scale = 320 / width
                new_width = 320
                new_height = int(height * scale)
                gray_resized = cv2.resize(gray, (new_width, new_height))
            else:
                gray_resized = gray.copy()
                scale = 1.0
            
            # STABILITY FIX: More conservative detection parameters
            boxes, weights = self.hog.detectMultiScale(
                gray_resized,
                winStride=(6, 6),        # Compromise between (4,4) and (8,8)
                padding=(12, 12),        # Compromise between (8,8) and (16,16)
                scale=1.03               # Slightly smaller step for better detection
            )
            
            # Scale boxes back to original size
            if scale != 1.0:
                boxes = [(int(x/scale), int(y/scale), int(w/scale), int(h/scale)) 
                        for x, y, w, h in boxes]
            
            # SPEED OPTIMIZATION: Simplified filtering for faster processing
            confident_boxes = []
            for i, (x, y, w, h) in enumerate(boxes):
                # Relaxed confidence threshold for speed
                if weights[i] > 0.2:  # Lowered from 0.3 for faster detection
                    # Basic size filtering only
                    if w > 20 and h > 40:  # Simplified from complex aspect ratio check
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
        
        # PID controller parameters - OPTIMIZED for faster response
        self.pid_x = PIDController(kp=0.6, ki=0.05, kd=0.1)      # Increased kp for faster response
        self.pid_distance = PIDController(kp=0.4, ki=0.02, kd=0.05)  # Increased kp, reduced kd
        
        # Frame dimensions (will be set when camera starts)
        self.frame_width = 640
        self.frame_height = 480
        
        # Target parameters
        self.target_x = self.frame_width // 2  # Center of frame
        self.target_distance = 150  # Target human height in pixels
        
        # SPEED OPTIMIZED control parameters
        self.max_turn_speed = 80      # Increased from 60 for faster response
        self.max_forward_speed = 90   # Increased from 80 for faster response
        
        # Edge detection and compensation
        self.edge_threshold = 80      # Reduced from 100 for faster edge response
        self.last_valid_center = None
        self.frames_since_detection = 0
        self.max_frames_without_detection = 5  # Reduced from 10 for faster timeout
        
        # STABILITY FIX: Add detection confidence tracking
        self.recent_detections = []
        self.detection_history_length = 5
        
        # SPEED OPTIMIZATION: Reduced movement smoothing
        self.movement_history = []
        self.history_length = 2       # Reduced from 3 for faster response
        
        # STABILITY FIX: Disable frame skipping to prevent false detection loss
        self.frame_skip_count = 0
        self.process_every_n_frames = 1  # Process every frame for stability
        
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
        
        # STABILITY FIX: Reset detection tracking
        self.recent_detections.clear()
        
        while self.tracking:
            try:
                # Get current frame
                frame = self.camera_manager.get_frame()
                if frame is None:
                    continue
                
                # Update frame dimensions
                self.frame_height, self.frame_width = frame.shape[:2]
                self.target_x = self.frame_width // 2
                
                # STABILITY FIX: Always process for reliable detection
                human_boxes = self.detector.detect_humans(frame)
                
                if human_boxes:
                    # STABILITY FIX: Track detection confidence
                    self.recent_detections.append(True)
                    if len(self.recent_detections) > self.detection_history_length:
                        self.recent_detections.pop(0)
                    
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
                    
                    # Calculate control commands FIRST for speed
                    self._track_human(center_x, human_height)
                    
                    # SPEED OPTIMIZATION: Simplified visualization
                    # Main bounding box only
                    cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
                    
                    # Center point
                    cv2.circle(frame, (center_x, center_y), 5, (0, 0, 255), -1)
                    
                    # Target center line
                    cv2.line(frame, (self.target_x, 0), (self.target_x, self.frame_height), (255, 0, 0), 1)
                    
                    # SPEED OPTIMIZATION: Minimal status text
                    x_error = center_x - self.target_x
                    cv2.putText(frame, f"TRACKING: X={x_error:+.0f}", (10, 30), 
                               cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
                    # SPEED OPTIMIZATION: Minimal status text only
                    distance_error = self.target_distance - human_height
                    direction = "→" if x_error > 0 else "←" if x_error < 0 else "●"
                    cv2.putText(frame, f"FAST TRACK {direction}: X={x_error:+.0f} D={distance_error:+.0f}", 
                               (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
                    
                else:
                    # STABILITY FIX: Track no detection and check if it's really lost
                    self.recent_detections.append(False)
                    if len(self.recent_detections) > self.detection_history_length:
                        self.recent_detections.pop(0)
                    
                    # Only trigger search if consistently losing detection
                    recent_detection_rate = sum(self.recent_detections) / len(self.recent_detections)
                    
                    if recent_detection_rate < 0.3:  # Less than 30% detection in recent frames
                        # Actually lost, use improved search behavior
                        self._handle_no_detection()
                    else:
                        # Probably just a brief blip, keep last movement briefly then stop
                        if self.frames_since_detection < 2:
                            # Keep current movement for 1-2 frames
                            pass  # Don't change motor commands
                        else:
                            # Stop after brief continuation
                            self.motor_controller.stop()
                    
                    with self.lock:
                        self.last_human_center = None
                    
                    # SPEED OPTIMIZATION: Minimal search indicator
                    detection_pct = int(recent_detection_rate * 100)
                    cv2.putText(frame, f"DETECTION: {detection_pct}% ({self.frames_since_detection})", 
                               (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
                
                # SPEED OPTIMIZATION: Skip extra frame info drawing
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
        Control car movement to track human with OPTIMIZED SPEED.
        
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
            
            # SPEED OPTIMIZATION: Simplified edge detection
            is_at_edge = center_x < self.edge_threshold or center_x > (self.frame_width - self.edge_threshold)
            
            # Calculate control outputs
            turn_output = self.pid_x.update(x_error)
            speed_output = self.pid_distance.update(distance_error)
            
            # SPEED OPTIMIZATION: Simplified adaptive scaling
            if is_at_edge:
                turn_scale = 0.7  # Less aggressive reduction for faster response
                speed_scale = 0.8
            else:
                turn_scale = 1.0
                speed_scale = 1.0
            
            # Calculate speeds with scaling
            forward_speed = max(-self.max_forward_speed, min(self.max_forward_speed, speed_output * speed_scale))
            turn_speed = max(-self.max_turn_speed, min(self.max_turn_speed, turn_output * turn_scale))
            
            # SPEED OPTIMIZATION: Reduced deadzones for faster response
            x_deadzone = 25 if is_at_edge else 20      # Reduced from 50/30
            distance_deadzone = 15 if is_at_edge else 10  # Reduced from 25/20
            
            if abs(x_error) < x_deadzone:
                turn_speed = 0
            if abs(distance_error) < distance_deadzone:
                forward_speed = 0
            
            # SPEED OPTIMIZATION: Minimal movement smoothing
            current_movement = (forward_speed, turn_speed)
            self.movement_history.append(current_movement)
            if len(self.movement_history) > self.history_length:
                self.movement_history.pop(0)
            
            # Light smoothing only when multiple samples available
            if len(self.movement_history) >= 2:
                avg_forward = sum(m[0] for m in self.movement_history) / len(self.movement_history)
                avg_turn = sum(m[1] for m in self.movement_history) / len(self.movement_history)
                
                # Less smoothing for faster response
                smooth_factor = 0.3  # Reduced from 0.7/0.3
                forward_speed = smooth_factor * avg_forward + (1 - smooth_factor) * forward_speed
                turn_speed = smooth_factor * avg_turn + (1 - smooth_factor) * turn_speed
            
            # Send commands to motor controller immediately
            self.motor_controller.move_with_turn(forward_speed, turn_speed)
            
            # Simplified logging for speed
            logger.info(f"FAST_TRACK: x_err={x_error:+3.0f}, dist_err={distance_error:+3.0f}, "
                       f"turn={turn_speed:+3.0f}, speed={forward_speed:+3.0f}")
                        
        except Exception as e:
            logger.error(f"Error in human tracking control: {e}")
            
    def _handle_no_detection(self):
        """Handle case when no human is detected - FIXED to prevent spinning."""
        self.frames_since_detection += 1
        
        # FIXED: Much more conservative search behavior
        if self.frames_since_detection <= 2:
            # For first 2 frames, just stop and wait - often temporary detection loss
            self.motor_controller.stop()
            logger.info("BRIEF LOSS: Stopping and waiting (probably temporary)")
            
        elif self.frames_since_detection <= self.max_frames_without_detection:
            # Only search after multiple frames of loss, and very gently
            if self.last_valid_center is not None:
                # Much smaller search movements to prevent spinning
                center_error = self.last_valid_center - self.target_x
                
                if abs(center_error) > 100:  # Only search if human was far from center
                    if center_error < 0:
                        # Human was significantly left, tiny left search
                        self.motor_controller.move_with_turn(0, -10)  # Reduced from -20
                        logger.info("SEARCHING: Tiny left search")
                    else:
                        # Human was significantly right, tiny right search  
                        self.motor_controller.move_with_turn(0, 10)   # Reduced from 20
                        logger.info("SEARCHING: Tiny right search")
                else:
                    # Human was near center when lost, just stop
                    self.motor_controller.stop()
                    logger.info("SEARCHING: Was centered, stopping")
            else:
                # No previous position, definitely stop
                self.motor_controller.stop()
                logger.info("SEARCHING: No history, stopping")
        else:
            # Been too long without detection, stop completely
            self.motor_controller.stop()
            self.movement_history.clear()  # Reset movement history
            logger.info("LOST: Stopping after extended search")
            
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