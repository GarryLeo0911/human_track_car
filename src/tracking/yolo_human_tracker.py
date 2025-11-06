"""
YOLOv8-based Human Detection and Tracking Module
Uses YOLOv8n for superior human detection accuracy.
"""

import cv2
import numpy as np
import logging
from threading import Lock
from typing import Tuple, Optional, List
import time

logger = logging.getLogger(__name__)

# Try to import YOLOv8
try:
    from ultralytics import YOLO
    YOLO_AVAILABLE = True
except ImportError as e:
    logger.warning(f"YOLOv8 not available: {e}. Falling back to HOG detector.")
    YOLO_AVAILABLE = False

class YOLOHumanDetector:
    """Human detection using YOLOv8n model."""
    
    def __init__(self):
        """Initialize the YOLOv8n model for human detection."""
        if not YOLO_AVAILABLE:
            raise ImportError("YOLOv8 (ultralytics) not available. Please install: pip install ultralytics")
        
        try:
            # Load YOLOv8n model (automatically downloads on first use)
            logger.info("Loading YOLOv8n model...")
            self.model = YOLO('yolov8n.pt')
            
            # Configure model for optimal performance
            self.model.overrides['verbose'] = False  # Reduce logging
            
            # COCO class ID for person
            self.person_class_id = 0
            
            # Detection parameters
            self.confidence_threshold = 0.5
            self.iou_threshold = 0.4
            
            # Detection history for stability
            self.detection_buffer = []
            self.buffer_size = 3
            
            logger.info("YOLOv8n model loaded successfully")
            
        except Exception as e:
            logger.error(f"Failed to load YOLOv8n model: {e}")
            raise
    
    def detect_humans(self, frame: np.ndarray) -> List[Tuple[int, int, int, int, float]]:
        """
        Detect humans in the frame using YOLOv8n.
        
        Args:
            frame: Input frame from camera
            
        Returns:
            List of bounding boxes (x, y, w, h, confidence) for detected humans
        """
        try:
            # Run YOLOv8 inference
            results = self.model(
                frame,
                conf=self.confidence_threshold,
                iou=self.iou_threshold,
                classes=[self.person_class_id],  # Only detect persons
                device='cpu',  # Use CPU for Raspberry Pi compatibility
                verbose=False
            )
            
            human_detections = []
            
            # Process results
            if results and len(results) > 0:
                result = results[0]  # Get first result
                
                if result.boxes is not None and len(result.boxes) > 0:
                    boxes = result.boxes.xyxy.cpu().numpy()  # Get bounding boxes
                    confidences = result.boxes.conf.cpu().numpy()  # Get confidences
                    
                    for i, (box, conf) in enumerate(zip(boxes, confidences)):
                        x1, y1, x2, y2 = box.astype(int)
                        
                        # Convert to (x, y, w, h) format
                        x, y = x1, y1
                        w, h = x2 - x1, y2 - y1
                        
                        # Validate detection
                        if self._is_valid_human_detection(x, y, w, h, conf, frame.shape):
                            human_detections.append((x, y, w, h, float(conf)))
            
            # Apply temporal filtering for stability
            filtered_detections = self._apply_temporal_filtering(human_detections)
            
            return filtered_detections
            
        except Exception as e:
            logger.error(f"Error in YOLOv8 human detection: {e}")
            return []
    
    def _is_valid_human_detection(self, x: int, y: int, w: int, h: int, 
                                conf: float, frame_shape: tuple) -> bool:
        """
        Validate if detection is a reasonable human detection.
        
        Args:
            x, y, w, h: Bounding box coordinates
            conf: Detection confidence
            frame_shape: (height, width, channels) of the frame
            
        Returns:
            True if detection is valid
        """
        frame_height, frame_width = frame_shape[:2]
        
        # Check if bounding box is within frame
        if x < 0 or y < 0 or x + w > frame_width or y + h > frame_height:
            return False
        
        # Size validation
        min_width, max_width = 20, frame_width // 2
        min_height, max_height = 40, frame_height
        
        if not (min_width <= w <= max_width and min_height <= h <= max_height):
            return False
        
        # Aspect ratio validation (humans are typically taller than wide)
        aspect_ratio = h / w if w > 0 else 0
        if not (1.2 <= aspect_ratio <= 5.0):  # Reasonable human proportions
            return False
        
        # Area validation (not too small or too large)
        area = w * h
        frame_area = frame_width * frame_height
        min_area = frame_area * 0.001  # At least 0.1% of frame
        max_area = frame_area * 0.8    # At most 80% of frame
        
        if not (min_area <= area <= max_area):
            return False
        
        return True
    
    def _apply_temporal_filtering(self, current_detections: List[Tuple[int, int, int, int, float]]) -> List[Tuple[int, int, int, int, float]]:
        """
        Apply temporal filtering to reduce detection noise.
        
        Args:
            current_detections: Current frame detections
            
        Returns:
            Filtered detections
        """
        # Add current detections to buffer
        self.detection_buffer.append(current_detections)
        if len(self.detection_buffer) > self.buffer_size:
            self.detection_buffer.pop(0)
        
        # If we don't have enough history, return current detections
        if len(self.detection_buffer) < 2:
            return current_detections
        
        # Filter detections based on temporal consistency
        stable_detections = []
        
        for detection in current_detections:
            x, y, w, h, conf = detection
            center_x, center_y = x + w // 2, y + h // 2
            
            # Check if this detection is consistent with recent history
            is_consistent = False
            
            for prev_detections in self.detection_buffer[:-1]:
                for prev_detection in prev_detections:
                    px, py, pw, ph, _ = prev_detection
                    prev_center_x, prev_center_y = px + pw // 2, py + ph // 2
                    
                    # Calculate distance between detection centers
                    distance = np.sqrt((center_x - prev_center_x)**2 + (center_y - prev_center_y)**2)
                    
                    # If centers are close enough, consider it consistent
                    if distance < 80:  # pixels
                        is_consistent = True
                        break
                
                if is_consistent:
                    break
            
            # Include detection if consistent or if confidence is very high
            if is_consistent or conf > 0.8:
                stable_detections.append(detection)
        
        return stable_detections


class YOLOHumanTracker:
    """Main human tracking system using YOLOv8."""
    
    def __init__(self, camera_manager, motor_controller):
        """
        Initialize the YOLO-based human tracker.
        
        Args:
            camera_manager: Camera management instance
            motor_controller: Motor control instance
        """
        self.camera_manager = camera_manager
        self.motor_controller = motor_controller
        
        # Try to initialize YOLO detector, fallback to HOG if needed
        try:
            self.detector = YOLOHumanDetector()
            self.detector_type = "YOLOv8n"
            logger.info("Using YOLOv8n for human detection")
        except Exception as e:
            logger.warning(f"Failed to initialize YOLOv8: {e}")
            logger.info("Falling back to HOG detector")
            from .human_tracker import HumanDetector
            self.detector = HumanDetector()
            self.detector_type = "HOG"
        
        # Tracking state
        self.tracking = False
        self.lock = Lock()
        self.last_human_center = None
        
        # PID controller parameters - TUNED FOR SMOOTH MOVEMENT
        self.pid_x = PIDController(kp=0.25, ki=0.01, kd=0.08)      # Reduced Kp for gentler turning
        self.pid_distance = PIDController(kp=0.20, ki=0.005, kd=0.05)  # Reduced Kp for gentler forward/back
        
        # Frame dimensions (will be set when camera starts)
        self.frame_width = 640
        self.frame_height = 480
        
        # Target parameters
        self.target_x = self.frame_width // 2
        self.target_distance = 150  # Target human height in pixels
        
        # Control parameters - REDUCED FOR SMOOTH MOVEMENT
        self.max_turn_speed = 35      # Reduced from 70 to 35 for gentler turns
        self.max_forward_speed = 50   # Reduced from 85 to 50 for gentler approach/retreat
        
        # Edge detection and compensation
        self.edge_threshold = 80
        self.last_valid_center = None
        self.frames_since_detection = 0
        self.max_frames_without_detection = 8  # Can be more patient with YOLO
        
        # Detection confidence tracking
        self.recent_detections = []
        self.detection_history_length = 5
        
        # Movement smoothing - ENHANCED FOR STABILITY
        self.movement_history = []
        self.history_length = 5       # Increased from 3 to 5 for more smoothing
        
        # Performance tracking
        self.detection_times = []
        self.max_time_samples = 30
        
        # Previous speeds for smooth transitions
        self.prev_forward_speed = 0
        self.prev_turn_speed = 0
    
    def start_tracking(self):
        """Start the human tracking loop."""
        logger.info(f"Starting human tracking with {self.detector_type}...")
        self.tracking = True
        
        # Reset controllers
        self.pid_x.reset()
        self.pid_distance.reset()
        self.movement_history.clear()
        self.frames_since_detection = 0
        self.last_valid_center = None
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
                
                # Detect humans with timing
                start_time = time.time()
                
                if self.detector_type == "YOLOv8n":
                    human_detections = self.detector.detect_humans(frame)
                    # Convert to format compatible with tracking logic
                    human_boxes = []
                    confidences = []
                    for detection in human_detections:
                        if len(detection) == 5:  # YOLO format (x, y, w, h, conf)
                            x, y, w, h, conf = detection
                            human_boxes.append((x, y, w, h))
                            confidences.append(conf)
                        else:  # Fallback format (x, y, w, h)
                            human_boxes.append(detection)
                            confidences.append(0.6)
                else:
                    human_boxes = self.detector.detect_humans(frame)
                    confidences = [0.6] * len(human_boxes)  # Default confidence for HOG
                
                detection_time = (time.time() - start_time) * 1000
                self._update_performance_stats(detection_time)
                
                if human_boxes:
                    # Track successful detection
                    self.recent_detections.append(True)
                    if len(self.recent_detections) > self.detection_history_length:
                        self.recent_detections.pop(0)
                    
                    # Select the best detection (highest confidence or largest)
                    if self.detector_type == "YOLOv8n" and confidences:
                        best_idx = np.argmax(confidences)
                        best_box = human_boxes[best_idx]
                        best_conf = confidences[best_idx]
                    else:
                        # For HOG or when no confidences, select largest
                        best_box = max(human_boxes, key=lambda box: box[2] * box[3])
                        best_conf = confidences[0] if confidences else 0.6
                    
                    # Ensure best_box is in correct format
                    if len(best_box) >= 4:
                        x, y, w, h = best_box[:4]  # Take first 4 elements
                    else:
                        continue  # Skip invalid detection
                    
                    # Calculate center and track
                    center_x = x + w // 2
                    center_y = y + h // 2
                    human_height = h
                    
                    # Update tracking state
                    with self.lock:
                        self.last_human_center = (center_x, center_y, human_height)
                    
                    # Control car movement
                    self._track_human(center_x, human_height)
                    
                    # Enhanced visualization for YOLO
                    self._draw_enhanced_visualization(frame, x, y, w, h, center_x, center_y, 
                                                   best_conf, detection_time)
                    
                else:
                    # Handle no detection
                    self.recent_detections.append(False)
                    if len(self.recent_detections) > self.detection_history_length:
                        self.recent_detections.pop(0)
                    
                    recent_detection_rate = sum(self.recent_detections) / len(self.recent_detections)
                    
                    if recent_detection_rate < 0.25:  # Less than 25% recent detections
                        self._handle_no_detection()
                    else:
                        # Brief loss, wait a bit longer with YOLO's accuracy
                        if self.frames_since_detection < 4:
                            pass  # Keep current movement
                        else:
                            self.motor_controller.stop()
                    
                    with self.lock:
                        self.last_human_center = None
                    
                    # Status display
                    detection_pct = int(recent_detection_rate * 100)
                    avg_time = sum(self.detection_times) / len(self.detection_times) if self.detection_times else 0
                    cv2.putText(frame, f"{self.detector_type} SEARCHING: {detection_pct}% | {avg_time:.1f}ms", 
                               (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
                
                # Update camera with processed frame
                self.camera_manager.set_processed_frame(frame)
                
            except Exception as e:
                logger.error(f"Error in YOLO tracking loop: {e}")
    
    def _draw_enhanced_visualization(self, frame, x, y, w, h, center_x, center_y, 
                                   confidence, detection_time):
        """Draw enhanced visualization for YOLO detections."""
        # Color based on confidence
        if confidence > 0.8:
            color = (0, 255, 0)  # Green for high confidence
        elif confidence > 0.6:
            color = (0, 255, 255)  # Yellow for medium confidence
        else:
            color = (0, 165, 255)  # Orange for lower confidence
        
        # Bounding box with confidence-based thickness
        thickness = 3 if confidence > 0.7 else 2
        cv2.rectangle(frame, (x, y), (x + w, y + h), color, thickness)
        
        # Center point
        cv2.circle(frame, (center_x, center_y), 6, color, -1)
        cv2.circle(frame, (center_x, center_y), 12, color, 2)
        
        # Target center line
        cv2.line(frame, (self.target_x, 0), (self.target_x, self.frame_height), (255, 0, 0), 2)
        
        # Status information
        x_error = center_x - self.target_x
        distance_error = self.target_distance - h
        direction = "→" if x_error > 0 else "←" if x_error < 0 else "●"
        
        # Performance info
        avg_time = sum(self.detection_times) / len(self.detection_times) if self.detection_times else detection_time
        
        cv2.putText(frame, f"{self.detector_type} TRACKING {direction}: X={x_error:+.0f} D={distance_error:+.0f}", 
                   (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
        cv2.putText(frame, f"Confidence: {confidence:.2f} | {avg_time:.1f}ms", 
                   (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
        cv2.putText(frame, f"Size: {w}x{h}", 
                   (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)
    
    def _track_human(self, center_x: int, human_height: int):
        """Control car movement to track human."""
        try:
            # Reset detection counter
            self.frames_since_detection = 0
            self.last_valid_center = center_x
            
            # Calculate errors
            x_error = center_x - self.target_x
            distance_error = self.target_distance - human_height
            
            # Edge detection
            is_at_edge = center_x < self.edge_threshold or center_x > (self.frame_width - self.edge_threshold)
            
            # PID control
            turn_output = self.pid_x.update(x_error)
            speed_output = self.pid_distance.update(distance_error)
            
            # Adaptive scaling based on edge position AND centering accuracy
            if is_at_edge:
                turn_scale = 0.8
                speed_scale = 0.9
            else:
                turn_scale = 1.0
                speed_scale = 1.0
            
            # ADDITIONAL: Gentle scaling based on how centered the human is
            center_factor = abs(x_error) / (self.frame_width / 2)  # 0.0 = perfectly centered, 1.0 = at edge
            center_factor = min(1.0, center_factor)  # Cap at 1.0
            
            # Reduce turn speed when human is already mostly centered
            if center_factor < 0.3:  # Within 30% of center
                turn_scale *= 0.5  # Very gentle movements when close to center
            elif center_factor < 0.6:  # Within 60% of center  
                turn_scale *= 0.7  # Moderately gentle movements
            
            # Apply scaling and limits
            forward_speed = max(-self.max_forward_speed, 
                              min(self.max_forward_speed, speed_output * speed_scale))
            turn_speed = max(-self.max_turn_speed, 
                           min(self.max_turn_speed, turn_output * turn_scale))
            
            # Deadzones - ENLARGED FOR STABILITY (less twitchy)
            x_deadzone = 40      # Increased from 20 to 40 for larger center zone
            distance_deadzone = 20  # Increased from 12 to 20 for stable distance
            
            if abs(x_error) < x_deadzone:
                turn_speed = 0
            if abs(distance_error) < distance_deadzone:
                forward_speed = 0
            
            # Movement smoothing
            current_movement = (forward_speed, turn_speed)
            self.movement_history.append(current_movement)
            if len(self.movement_history) > self.history_length:
                self.movement_history.pop(0)
            
            # Apply smoothing - ENHANCED FOR SMOOTH MOVEMENT
            if len(self.movement_history) >= 2:
                avg_forward = sum(m[0] for m in self.movement_history) / len(self.movement_history)
                avg_turn = sum(m[1] for m in self.movement_history) / len(self.movement_history)
                
                smooth_factor = 0.7  # Increased from 0.4 to 0.7 for much more smoothing
                forward_speed = smooth_factor * avg_forward + (1 - smooth_factor) * forward_speed
                turn_speed = smooth_factor * avg_turn + (1 - smooth_factor) * turn_speed
                
                # Additional gentle limiting to prevent sudden changes
                max_change_per_frame = 10  # Maximum change in speed per frame
                if hasattr(self, 'prev_forward_speed'):
                    forward_diff = forward_speed - self.prev_forward_speed
                    if abs(forward_diff) > max_change_per_frame:
                        forward_speed = self.prev_forward_speed + (max_change_per_frame if forward_diff > 0 else -max_change_per_frame)
                        
                if hasattr(self, 'prev_turn_speed'):
                    turn_diff = turn_speed - self.prev_turn_speed
                    if abs(turn_diff) > max_change_per_frame:
                        turn_speed = self.prev_turn_speed + (max_change_per_frame if turn_diff > 0 else -max_change_per_frame)
                
                # Store for next frame
                self.prev_forward_speed = forward_speed
                self.prev_turn_speed = turn_speed
            
            # Send commands
            self.motor_controller.move_with_turn(forward_speed, turn_speed)
            
            logger.debug(f"YOLO_TRACK: x_err={x_error:+3.0f}, dist_err={distance_error:+3.0f}, "
                        f"turn={turn_speed:+3.0f}, speed={forward_speed:+3.0f}")
            
        except Exception as e:
            logger.error(f"Error in YOLO tracking control: {e}")
    
    def _handle_no_detection(self):
        """Handle case when no human is detected."""
        self.frames_since_detection += 1
        
        if self.frames_since_detection <= 3:
            # Stop and wait - YOLO is accurate, probably actually lost
            self.motor_controller.stop()
            logger.debug("YOLO: Brief loss, stopping")
        elif self.frames_since_detection <= self.max_frames_without_detection:
            # Gentle search only if we had a clear direction
            if self.last_valid_center is not None:
                center_error = self.last_valid_center - self.target_x
                if abs(center_error) > 80:  # Only search if significantly off-center
                    search_speed = 15  # Very gentle search
                    if center_error < 0:
                        self.motor_controller.move_with_turn(0, -search_speed)
                    else:
                        self.motor_controller.move_with_turn(0, search_speed)
                    logger.debug("YOLO: Gentle search")
                else:
                    self.motor_controller.stop()
            else:
                self.motor_controller.stop()
        else:
            # Stop after extended search
            self.motor_controller.stop()
            self.movement_history.clear()
            logger.debug("YOLO: Extended loss, stopping")
    
    def _update_performance_stats(self, detection_time):
        """Update performance statistics."""
        self.detection_times.append(detection_time)
        if len(self.detection_times) > self.max_time_samples:
            self.detection_times.pop(0)
    
    def stop_tracking(self):
        """Stop the human tracking."""
        logger.info("Stopping YOLO human tracking...")
        self.tracking = False
        self.motor_controller.stop()
    
    def get_tracking_status(self) -> dict:
        """Get current tracking status."""
        with self.lock:
            avg_time = sum(self.detection_times) / len(self.detection_times) if self.detection_times else 0
            return {
                'tracking': self.tracking,
                'detector_type': self.detector_type,
                'last_human_center': self.last_human_center,
                'target_center': (self.target_x, self.frame_height // 2),
                'frame_size': (self.frame_width, self.frame_height),
                'avg_detection_time': avg_time,
                'recent_detection_rate': sum(self.recent_detections) / len(self.recent_detections) if self.recent_detections else 0
            }


class PIDController:
    """Simple PID controller implementation."""
    
    def __init__(self, kp: float, ki: float, kd: float):
        self.kp = kp
        self.ki = ki
        self.kd = kd
        self.previous_error = 0
        self.integral = 0
        
    def update(self, error: float) -> float:
        # Proportional term
        p_term = self.kp * error
        
        # Integral term with windup protection
        self.integral += error
        # Prevent integral windup
        max_integral = 100
        self.integral = max(-max_integral, min(max_integral, self.integral))
        i_term = self.ki * self.integral
        
        # Derivative term
        derivative = error - self.previous_error
        d_term = self.kd * derivative
        
        self.previous_error = error
        
        return p_term + i_term + d_term
    
    def reset(self):
        self.previous_error = 0
        self.integral = 0