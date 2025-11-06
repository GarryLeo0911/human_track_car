"""
Human Detection and Tracking Module
Handles detection and tracking of humans using computer vision.
"""

import cv2
import numpy as np
import logging
import time
from threading import Lock
from typing import Tuple, Optional, List

logger = logging.getLogger(__name__)

class HumanDetector:
    """Human detection using HOG descriptor with improved accuracy."""
    
    def __init__(self):
        """Initialize the HOG descriptor for human detection."""
        self.hog = cv2.HOGDescriptor()
        # Use numpy array for the detector
        import numpy as np
        detector = cv2.HOGDescriptor.getDefaultPeopleDetector()
        self.hog.setSVMDetector(np.array(detector, dtype=np.float32))
        
        # Detection history for stability
        self.detection_buffer = []
        self.buffer_size = 3
        
    def detect_humans(self, frame: np.ndarray) -> List[Tuple[int, int, int, int]]:
        """
        Detect humans in the frame with improved accuracy.
        
        Args:
            frame: Input frame from camera
            
        Returns:
            List of bounding boxes (x, y, w, h) for detected humans
        """
        try:
            # Preprocess frame for better detection
            height, width = frame.shape[:2]
            
            # Convert to grayscale for HOG
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            
            # ACCURACY IMPROVEMENT: Apply contrast enhancement for better detection
            gray = cv2.equalizeHist(gray)
            
            # ACCURACY IMPROVEMENT: Apply noise reduction
            gray = cv2.GaussianBlur(gray, (3, 3), 0)
            
            # ACCURACY IMPROVEMENT: Less aggressive resizing for better detection
            if width > 480:  # Increased from 320 back to 480 for better accuracy
                scale = 480 / width
                new_width = 480
                new_height = int(height * scale)
                gray_resized = cv2.resize(gray, (new_width, new_height))
            else:
                gray_resized = gray.copy()
                scale = 1.0
            
            # ACCURACY IMPROVEMENT: Better detection parameters
            boxes, weights = self.hog.detectMultiScale(
                gray_resized,
                winStride=(4, 4),        # Smaller stride for better detection
                padding=(8, 8),          # Standard padding
                scale=1.02               # Smaller scale step for more thorough detection
            )
            
            # Scale boxes back to original size
            if scale != 1.0:
                boxes = [(int(x/scale), int(y/scale), int(w/scale), int(h/scale)) 
                        for x, y, w, h in boxes]
            
            # ACCURACY IMPROVEMENT: Better filtering with proper validation
            confident_boxes = []
            for i, (x, y, w, h) in enumerate(boxes):
                # Higher confidence threshold for better accuracy
                if weights[i] > 0.4:  # Increased from 0.2 to 0.4 for better quality
                    # Proper size and aspect ratio validation
                    aspect_ratio = h / w if w > 0 else 0
                    
                    # Human-like proportions (height should be 1.5-4x width)
                    if (w > 30 and h > 60 and  # Minimum size requirements
                        aspect_ratio >= 1.5 and aspect_ratio <= 4.0 and  # Human proportions
                        x >= 0 and y >= 0 and x + w <= width and y + h <= height):  # Within frame
                        confident_boxes.append((x, y, w, h))
            
            # ACCURACY IMPROVEMENT: Temporal consistency filtering
            self.detection_buffer.append(confident_boxes)
            if len(self.detection_buffer) > self.buffer_size:
                self.detection_buffer.pop(0)
            
            # Return stabilized detections
            return self._stabilize_detections()
            
        except Exception as e:
            logger.error(f"Error in human detection: {e}")
            return []
    
    def _stabilize_detections(self) -> List[Tuple[int, int, int, int]]:
        """
        Stabilize detections using temporal information.
        
        Returns:
            Stabilized list of detections
        """
        if not self.detection_buffer:
            return []
        
        # Get the most recent detections
        current_detections = self.detection_buffer[-1]
        
        # If we have enough history, validate against previous frames
        if len(self.detection_buffer) >= 2:
            stable_detections = []
            
            for current_box in current_detections:
                x, y, w, h = current_box
                center_x, center_y = x + w//2, y + h//2
                
                # Check if this detection is consistent with recent history
                is_stable = False
                for prev_detections in self.detection_buffer[:-1]:
                    for prev_box in prev_detections:
                        px, py, pw, ph = prev_box
                        prev_center_x, prev_center_y = px + pw//2, py + ph//2
                        
                        # Check if centers are close (within 50 pixels)
                        center_distance = ((center_x - prev_center_x)**2 + (center_y - prev_center_y)**2)**0.5
                        if center_distance < 50:
                            is_stable = True
                            break
                    
                    if is_stable:
                        break
                
                # Include detection if it's stable or if we don't have enough history
                if is_stable or len(self.detection_buffer) < 2:
                    stable_detections.append(current_box)
            
            return stable_detections
        else:
            return current_detections


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
        
        # PID controller parameters - INCREASED TURNING RESPONSIVENESS
        self.pid_x = PIDController(kp=0.25, ki=0.008, kd=0.08)    # Increased turning responsiveness
        self.pid_distance = PIDController(kp=0.12, ki=0.002, kd=0.03)  # Keep distance gentle
        
        # Frame dimensions (will be set when camera starts)
        self.frame_width = 640
        self.frame_height = 480
        
        # Target parameters - PERCENTAGE-BASED DISTANCE CONTROL
        self.target_x = self.frame_width // 2  # Center of frame
        self.target_human_percentage = 0.25  # Human should occupy 25% of frame height
        self.target_distance = int(self.frame_height * self.target_human_percentage)  # 120 pixels for 480p
        
        # SPEED OPTIMIZED control parameters - BALANCED SPEED FOR LONGER DURATION STEPS
        self.max_turn_speed = 50      # Reduced from 70 - moderate speed with longer duration
        self.max_forward_speed = 50   # Reduced from 60 - balanced speed
        
        # Edge detection and compensation - IMPROVED
        self.edge_threshold = 100     # Increased from 80 for earlier edge detection
        self.last_valid_center = None
        self.frames_since_detection = 0
        self.max_frames_without_detection = 5  # Reduced from 10 for faster timeout
        
        # Detection history and confidence tracking
        self.recent_detections = []
        self.detection_history_length = 7  # Increased for better stability
        
        # ACCURACY IMPROVEMENT: More conservative movement parameters
        self.movement_history = []
        self.history_length = 4       # Increased for smoother movement
        
        # Step-by-step turning configuration - BALANCED SPEED AND DURATION
        self.step_turn_enabled = True
        self.turn_step_angle = 15  # Degrees per step (small discrete turns)
        self.turn_step_duration = 0.8  # Increased from 0.3 for longer, more effective steps
        self.turn_pause_duration = 0.4  # Increased from 0.2 for better assessment time
        self.last_turn_step_time = 0
        self.is_in_turn_step = False
        self.current_turn_direction = 0  # -1 for left, 1 for right, 0 for none
        self.accumulated_turn_error = 0  # Track how much we still need to turn
        
        # ACCURACY IMPROVEMENT: Process every frame for maximum accuracy
        self.frame_skip_count = 0
        self.process_every_n_frames = 1  # Process every frame for accuracy
        
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
                    
                    # ACCURACY IMPROVEMENT: Enhanced visualization with detection quality
                    # Main bounding box with confidence color coding
                    confidence = max(0, min(1, (human_height - 40) / 160))  # Rough confidence based on size
                    color_intensity = int(255 * confidence)
                    bbox_color = (0, color_intensity, 255 - color_intensity)  # Green for good, red for poor
                    cv2.rectangle(frame, (x, y), (x + w, y + h), bbox_color, 2)
                    
                    # Center point with size indicator
                    cv2.circle(frame, (center_x, center_y), 5, (0, 0, 255), -1)
                    cv2.circle(frame, (center_x, center_y), int(confidence * 15 + 5), bbox_color, 2)
                    
                    # Target center line
                    cv2.line(frame, (self.target_x, 0), (self.target_x, self.frame_height), (255, 0, 0), 1)
                    
                    # ACCURACY IMPROVEMENT: Detailed status information
                    x_error = center_x - self.target_x
                    distance_error = self.target_distance - human_height
                    direction = "→" if x_error > 0 else "←" if x_error < 0 else "●"
                    
                    cv2.putText(frame, f"TRACKING {direction}: X={x_error:+.0f} D={distance_error:+.0f}", 
                               (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
                    cv2.putText(frame, f"Size: {w}x{h} Conf: {confidence:.2f}", 
                               (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.5, bbox_color, 2)
                    
                else:
                    # ACCURACY IMPROVEMENT: More conservative detection loss handling
                    self.recent_detections.append(False)
                    if len(self.recent_detections) > self.detection_history_length:
                        self.recent_detections.pop(0)
                    
                    # Only trigger search if consistently losing detection
                    recent_detection_rate = sum(self.recent_detections) / len(self.recent_detections)
                    
                    if recent_detection_rate < 0.2:  # Less than 20% detection in recent frames
                        # Actually lost, use improved search behavior
                        self._handle_no_detection()
                    else:
                        # Probably just a brief blip, keep last movement briefly then stop
                        if self.frames_since_detection < 3:  # Increased patience
                            # Keep current movement for a few more frames
                            pass  # Don't change motor commands
                        else:
                            # Stop after brief continuation
                            self.motor_controller.stop()
                    
                    with self.lock:
                        self.last_human_center = None
                    
                    # ACCURACY IMPROVEMENT: Better search indicator
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
            
            # Calculate errors - FIXED DISTANCE LOGIC
            x_error = center_x - self.target_x
            
            # PERCENTAGE-BASED DISTANCE CONTROL
            current_percentage = human_height / self.frame_height
            target_percentage = self.target_human_percentage
            distance_error = target_percentage - current_percentage  # Positive = need to get closer
            
            # Convert percentage error to pixel equivalent for PID
            distance_error_pixels = distance_error * self.frame_height
            
            # SPEED OPTIMIZATION: Simplified edge detection
            is_at_edge = center_x < self.edge_threshold or center_x > (self.frame_width - self.edge_threshold)
            
            # Calculate control outputs
            turn_output = self.pid_x.update(x_error)
            speed_output = self.pid_distance.update(distance_error_pixels)
            
            # Debug logging
            logger.debug(f"HOG_DISTANCE: current={current_percentage:.2%}, target={target_percentage:.2%}, "
                        f"error={distance_error:.3f}")
            
            # FIXED: Edge behavior prioritization
            if is_at_edge:
                # At edge: FORCE turning, minimize distance control
                turn_scale = 2.0     # STRONG turn response at edge
                speed_scale = 0.1    # Minimal forward movement at edge
            else:
                turn_scale = 1.0
                speed_scale = 1.0
            
            # FIXED: Priority-based movement logic
            center_factor = abs(x_error) / (self.frame_width / 2)  # 0.0 = perfectly centered, 1.0 = at edge
            center_factor = min(1.0, center_factor)  # Cap at 1.0
            
            # PRIORITIZE CENTERING: Reduce distance control when not centered, but allow some response
            if center_factor > 0.5:  # Very off-center 
                speed_scale *= 0.1  # Virtually disable forward movement
                # Increase turn responsiveness when off-center
                if center_factor > 0.7:  # Very off-center
                    turn_scale *= 1.2
                else:  # Moderately off-center
                    turn_scale *= 1.0
            elif center_factor > 0.3:  # Moderately off-center - allow some distance control
                speed_scale *= 0.4  # Reduce but don't eliminate forward movement
                turn_scale *= 1.0
            else:
                # Well centered - allow normal distance control
                if center_factor < 0.1:  # Very well centered
                    turn_scale *= 0.3  # Gentle turns when well centered
                elif center_factor < 0.2:  # Reasonably centered
                    turn_scale *= 0.5
            
            # Calculate speeds with scaling
            forward_speed = max(-self.max_forward_speed, min(self.max_forward_speed, speed_output * speed_scale))
            turn_speed = max(-self.max_turn_speed, min(self.max_turn_speed, turn_output * turn_scale))
            
            # FIXED deadzones for proper behavior with percentage-based distance
            x_deadzone = 40      # Pixels for centering
            distance_deadzone_percentage = 0.03  # 3% of frame height
            distance_deadzone_pixels = distance_deadzone_percentage * self.frame_height
            
            # Apply deadzones
            if abs(x_error) < x_deadzone:
                turn_speed = 0
            
            if abs(distance_error_pixels) < distance_deadzone_pixels:
                forward_speed = 0
            
            # ENHANCED EDGE OVERRIDE: Force turning at edge regardless of deadzone
            if is_at_edge and turn_speed == 0:
                # Force turn direction based on position at edge
                edge_turn_strength = 40  # Further increased from 30 for much stronger edge response
                if center_x < self.frame_width // 2:
                    turn_speed = -edge_turn_strength  # Turn left to center
                else:
                    turn_speed = edge_turn_strength   # Turn right to center
            
            # ENSURE STRONGER MINIMUM MOVEMENT to overcome motor resistance
            min_turn_threshold = 25  # Increased from 15 for stronger turning force
            min_forward_threshold = 18  # Increased from 12 for stronger forward force
            
            if turn_speed != 0:
                if 0 < abs(turn_speed) < min_turn_threshold:
                    turn_speed = min_turn_threshold if turn_speed > 0 else -min_turn_threshold
                    
            if forward_speed != 0:
                if 0 < abs(forward_speed) < min_forward_threshold:
                    forward_speed = min_forward_threshold if forward_speed > 0 else -min_forward_threshold
                forward_speed = 0
            
            # STEP-BY-STEP TURNING LOGIC for ultra-smooth movement with edge override
            current_time = time.time()
            
            if self.step_turn_enabled and (turn_speed != 0 or is_at_edge):
                # Handle step-by-step turning (allow at edge even if turn_speed was 0)
                if turn_speed == 0 and is_at_edge:
                    # Force turn direction based on position at edge
                    if center_x < self.frame_width // 2:
                        turn_speed = -15  # Turn left to center
                    else:
                        turn_speed = 15   # Turn right to center
                turn_speed = self._handle_step_turning(turn_speed, x_error, current_time)
            
            # SPEED OPTIMIZATION: Minimal movement smoothing (forward only, turning is stepped)
            current_movement = (forward_speed, 0 if self.step_turn_enabled else turn_speed)
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
    
    def _handle_step_turning(self, desired_turn_speed: float, x_error: int, current_time: float) -> float:
        """
        Handle step-by-step turning instead of continuous turning.
        
        Args:
            desired_turn_speed: The calculated turn speed from PID
            x_error: Current horizontal error in pixels
            current_time: Current timestamp
            
        Returns:
            Actual turn speed to apply (0 during pauses, stepped during turns)
        """
        # Determine desired turn direction
        if desired_turn_speed > 0:
            desired_direction = 1  # Right
        elif desired_turn_speed < 0:
            desired_direction = -1  # Left
        else:
            desired_direction = 0  # No turn needed
        
        # If we're currently in a turn step
        if self.is_in_turn_step:
            # Check if current step duration is complete
            if current_time - self.last_turn_step_time >= self.turn_step_duration:
                # Stop turning and start pause
                self.is_in_turn_step = False
                self.last_turn_step_time = current_time
                logger.debug(f"HOG_STEP_TURN: Completed step, starting pause")
                return 0
            else:
                # Continue current turn step with moderate speed for longer duration
                turn_speed = self.current_turn_direction * (self.max_turn_speed * 0.6)  # Moderate speed (60%)
                logger.debug(f"HOG_STEP_TURN: Continuing step, speed={turn_speed}")
                return turn_speed
        
        # If we're in a pause between steps
        elif self.current_turn_direction != 0:
            # Check if pause duration is complete
            if current_time - self.last_turn_step_time >= self.turn_pause_duration:
                # Decide if we need another step
                if abs(x_error) > 60:  # Still need to turn (outside deadzone)
                    if desired_direction == self.current_turn_direction:
                        # Continue in same direction with moderate speed
                        self.is_in_turn_step = True
                        self.last_turn_step_time = current_time
                        turn_speed = self.current_turn_direction * (self.max_turn_speed * 0.6)
                        logger.debug(f"HOG_STEP_TURN: Starting new step, same direction, speed={turn_speed}")
                        return turn_speed
                    else:
                        # Change direction or stop
                        self.current_turn_direction = desired_direction
                        if desired_direction != 0:
                            self.is_in_turn_step = True
                            self.last_turn_step_time = current_time
                            turn_speed = self.current_turn_direction * (self.max_turn_speed * 0.6)
                            logger.debug(f"HOG_STEP_TURN: Starting new step, new direction, speed={turn_speed}")
                            return turn_speed
                        else:
                            # No more turning needed
                            self.current_turn_direction = 0
                            logger.debug("HOG_STEP_TURN: Centered, stopping")
                            return 0
                else:
                    # Close enough to center, stop turning
                    self.current_turn_direction = 0
                    logger.debug("HOG_STEP_TURN: Within deadzone, stopping")
                    return 0
            else:
                # Still in pause
                logger.debug("HOG_STEP_TURN: In pause between steps")
                return 0
        
        # Not currently turning, check if we need to start
        else:
            if desired_direction != 0 and abs(x_error) > 60:  # Need to start turning
                self.current_turn_direction = desired_direction
                self.is_in_turn_step = True
                self.last_turn_step_time = current_time
                turn_speed = self.current_turn_direction * (self.max_turn_speed * 0.6)
                logger.debug(f"HOG_STEP_TURN: Starting first step, direction={desired_direction}, speed={turn_speed}")
                return turn_speed
            else:
                # No turning needed
                return 0
            
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