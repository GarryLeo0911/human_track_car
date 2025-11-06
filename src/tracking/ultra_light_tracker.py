"""
Ultra-Lightweight Human Detection and Tracking Module - Simplified Version
Minimalist human detection solutions designed for Raspberry Pi
"""

import cv2
import numpy as np
import logging
import time
from threading import Lock
from typing import Tuple, Optional, List

logger = logging.getLogger(__name__)

class MotionBasedDetector:
    """Ultra-lightweight human detector based on motion detection"""
    
    def __init__(self):
        """Initialize motion detector"""
        # Use simple frame difference method
        self.prev_frame = None
        self.motion_threshold = 25  # Motion threshold
        self.min_area = 1000       # Minimum detection area
        self.max_area = 20000      # Maximum detection area
        
        # Morphological operation kernel
        self.kernel = np.ones((5, 5), np.uint8)
        
        # Detection stability
        self.detection_history = []
        self.history_size = 3
        
        logger.info("Motion detector initialized")
    
    def detect_humans(self, frame: np.ndarray) -> List[Tuple[int, int, int, int]]:
        """
        Frame difference based motion detection
        
        Args:
            frame: Input frame
            
        Returns:
            List of detected bounding boxes (x, y, w, h)
        """
        try:
            # Convert to grayscale
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            gray = cv2.GaussianBlur(gray, (21, 21), 0)
            
            # If no previous frame, store current frame
            if self.prev_frame is None:
                self.prev_frame = gray
                return []
            
            # Calculate frame difference
            frame_diff = cv2.absdiff(self.prev_frame, gray)
            
            # Thresholding
            _, thresh = cv2.threshold(frame_diff, self.motion_threshold, 255, cv2.THRESH_BINARY)
            
            # Morphological operations
            thresh = cv2.dilate(thresh, self.kernel, iterations=2)
            thresh = cv2.erode(thresh, self.kernel, iterations=1)
            
            # Find contours
            contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            detections = []
            for contour in contours:
                area = cv2.contourArea(contour)
                if self.min_area < area < self.max_area:
                    x, y, w, h = cv2.boundingRect(contour)
                    
                    # Simple human proportion check
                    aspect_ratio = h / w if w > 0 else 0
                    if 0.5 < aspect_ratio < 3.0:  # Reasonable human proportions
                        detections.append((x, y, w, h))
            
            # Update previous frame
            self.prev_frame = gray.copy()
            
            # Apply temporal stability
            return self._stabilize_detections(detections)
            
        except Exception as e:
            logger.error(f"Motion detection error: {e}")
            return []
    
    def _stabilize_detections(self, detections: List[Tuple[int, int, int, int]]) -> List[Tuple[int, int, int, int]]:
        """Temporal stability filtering"""
        self.detection_history.append(detections)
        if len(self.detection_history) > self.history_size:
            self.detection_history.pop(0)
        
        if len(self.detection_history) < 2:
            return detections
        
        # Simple temporal consistency check
        stable_detections = []
        for detection in detections:
            x, y, w, h = detection
            center_x, center_y = x + w // 2, y + h // 2
            
            # Check if consistent with history
            for prev_detections in self.detection_history[:-1]:
                for prev_det in prev_detections:
                    px, py, pw, ph = prev_det
                    prev_center_x, prev_center_y = px + pw // 2, py + ph // 2
                    
                    # Calculate distance
                    distance = np.sqrt((center_x - prev_center_x)**2 + (center_y - prev_center_y)**2)
                    if distance < 80:  # Pixel distance threshold
                        stable_detections.append(detection)
                        break
        
        return stable_detections


class EdgeBasedDetector:
    """Lightweight human detector based on edge detection"""
    
    def __init__(self):
        """Initialize edge detector"""
        # Canny edge detection parameters
        self.canny_low = 50
        self.canny_high = 150
        
        # Contour filtering parameters
        self.min_contour_area = 800
        self.max_contour_area = 15000
        self.min_aspect_ratio = 0.4
        self.max_aspect_ratio = 2.5
        
        # Morphological operation kernel
        self.kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
        
        logger.info("Edge detector initialized")
    
    def detect_humans(self, frame: np.ndarray) -> List[Tuple[int, int, int, int]]:
        """
        Edge detection based human detection
        
        Args:
            frame: Input frame
            
        Returns:
            List of detected bounding boxes (x, y, w, h)
        """
        try:
            # Convert to grayscale
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            
            # Gaussian blur
            blurred = cv2.GaussianBlur(gray, (5, 5), 0)
            
            # Canny edge detection
            edges = cv2.Canny(blurred, self.canny_low, self.canny_high)
            
            # Morphological closing to connect edges
            edges = cv2.morphologyEx(edges, cv2.MORPH_CLOSE, self.kernel)
            edges = cv2.dilate(edges, self.kernel, iterations=2)
            
            # Find contours
            contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            detections = []
            for contour in contours:
                area = cv2.contourArea(contour)
                if self.min_contour_area < area < self.max_contour_area:
                    x, y, w, h = cv2.boundingRect(contour)
                    
                    # Aspect ratio check
                    aspect_ratio = w / h if h > 0 else 0
                    if self.min_aspect_ratio < aspect_ratio < self.max_aspect_ratio:
                        detections.append((x, y, w, h))
            
            return detections
            
        except Exception as e:
            logger.error(f"Edge detection error: {e}")
            return []


class ColorBasedDetector:
    """Lightweight human detector based on skin color detection"""
    
    def __init__(self):
        """Initialize skin color detector"""
        # HSV skin color range
        self.lower_skin = np.array([0, 20, 70], dtype=np.uint8)
        self.upper_skin = np.array([20, 255, 255], dtype=np.uint8)
        
        # Morphological operation kernel
        self.kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7))
        
        # Detection parameters
        self.min_area = 500
        self.max_area = 10000
        
        logger.info("Skin color detector initialized")
    
    def detect_humans(self, frame: np.ndarray) -> List[Tuple[int, int, int, int]]:
        """
        Skin color based human detection
        
        Args:
            frame: Input frame
            
        Returns:
            List of detected bounding boxes (x, y, w, h)
        """
        try:
            # Convert to HSV color space
            hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
            
            # Skin color mask
            skin_mask = cv2.inRange(hsv, self.lower_skin, self.upper_skin)
            
            # Morphological operations for noise reduction
            skin_mask = cv2.morphologyEx(skin_mask, cv2.MORPH_OPEN, self.kernel)
            skin_mask = cv2.morphologyEx(skin_mask, cv2.MORPH_CLOSE, self.kernel)
            
            # Find contours
            contours, _ = cv2.findContours(skin_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            detections = []
            for contour in contours:
                area = cv2.contourArea(contour)
                if self.min_area < area < self.max_area:
                    x, y, w, h = cv2.boundingRect(contour)
                    detections.append((x, y, w, h))
            
            return detections
            
        except Exception as e:
            logger.error(f"Skin color detection error: {e}")
            return []


class UltraLightHumanTracker:
    """Ultra-lightweight human tracker main class"""
    
    def __init__(self, camera_manager, motor_controller, detector_type='motion'):
        """
        Initialize ultra-lightweight human tracker
        
        Args:
            camera_manager: Camera manager instance
            motor_controller: Motor controller instance
            detector_type: Detector type ('motion', 'edge', 'color')
        """
        self.camera_manager = camera_manager
        self.motor_controller = motor_controller
        
        # Select detector
        if detector_type == 'motion':
            self.detector = MotionBasedDetector()
            self.detector_name = "Motion Detection"
        elif detector_type == 'edge':
            self.detector = EdgeBasedDetector()
            self.detector_name = "Edge Detection"
        elif detector_type == 'color':
            self.detector = ColorBasedDetector()
            self.detector_name = "Skin Color Detection"
        else:
            # Default to motion detection
            self.detector = MotionBasedDetector()
            self.detector_name = "Motion Detection"
        
        # Tracking state
        self.tracking = False
        self.lock = Lock()
        self.last_human_center = None
        
        # Simplified PID controllers
        self.pid_x = SimplePIDController(kp=0.4, ki=0.08, kd=0.15)
        self.pid_distance = SimplePIDController(kp=0.25, ki=0.03, kd=0.08)
        
        # Frame parameters
        self.frame_width = 640
        self.frame_height = 480
        self.target_x = self.frame_width // 2
        self.target_distance = 100  # Target human height
        
        # Control parameters
        self.max_turn_speed = 35
        self.max_forward_speed = 25
        
        # Detection failure handling
        self.frames_since_detection = 0
        self.max_frames_without_detection = 8
        
        # Movement smoothing
        self.movement_history = []
        self.history_length = 4
        
        logger.info(f"Ultra-lightweight human tracker initialized with {self.detector_name}")
    
    def start_tracking(self):
        """Start human tracking"""
        logger.info(f"Starting {self.detector_name} human tracking...")
        self.tracking = True
        
        # Reset controllers
        self.pid_x.reset()
        self.pid_distance.reset()
        self.frames_since_detection = 0
        self.movement_history.clear()
        
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
                start_time = time.time()
                human_detections = self.detector.detect_humans(frame)
                detection_time = (time.time() - start_time) * 1000
                
                if human_detections:
                    # Select the largest detection
                    best_detection = max(human_detections, key=lambda box: box[2] * box[3])
                    x, y, w, h = best_detection
                    
                    # Calculate center point
                    center_x = x + w // 2
                    center_y = y + h // 2
                    
                    # Update tracking state
                    with self.lock:
                        self.last_human_center = (center_x, center_y, h)
                    
                    # Control vehicle movement
                    self._track_human(center_x, h)
                    
                    # Visualization
                    self._draw_visualization(frame, x, y, w, h, center_x, center_y, detection_time)
                    
                    self.frames_since_detection = 0
                else:
                    # No human detected
                    self._handle_no_detection()
                    with self.lock:
                        self.last_human_center = None
                    
                    # Status display
                    cv2.putText(frame, f"{self.detector_name} Searching... {detection_time:.1f}ms", 
                               (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
                
                # Update camera with processed frame
                self.camera_manager.set_processed_frame(frame)
                
                # Control frame rate to reduce CPU load
                time.sleep(0.05)  # 20FPS
                
            except Exception as e:
                logger.error(f"Ultra-lightweight tracking loop error: {e}")
    
    def _track_human(self, center_x: int, human_height: int):
        """Control vehicle to track human"""
        try:
            # Calculate errors
            x_error = center_x - self.target_x
            distance_error = self.target_distance - human_height
            
            # PID control
            turn_output = self.pid_x.update(x_error)
            speed_output = self.pid_distance.update(distance_error)
            
            # Limit output
            turn_speed = max(-self.max_turn_speed, min(self.max_turn_speed, turn_output))
            forward_speed = max(-self.max_forward_speed, min(self.max_forward_speed, speed_output))
            
            # Deadzone handling
            if abs(x_error) < 40:
                turn_speed = 0
            if abs(distance_error) < 25:
                forward_speed = 0
            
            # Movement smoothing
            current_movement = (forward_speed, turn_speed)
            self.movement_history.append(current_movement)
            if len(self.movement_history) > self.history_length:
                self.movement_history.pop(0)
            
            if len(self.movement_history) >= 2:
                avg_forward = sum(m[0] for m in self.movement_history) / len(self.movement_history)
                avg_turn = sum(m[1] for m in self.movement_history) / len(self.movement_history)
                
                smooth_factor = 0.7
                forward_speed = smooth_factor * avg_forward + (1 - smooth_factor) * forward_speed
                turn_speed = smooth_factor * avg_turn + (1 - smooth_factor) * turn_speed
            
            # Send control command
            self.motor_controller.move_with_turn(forward_speed, turn_speed)
            
        except Exception as e:
            logger.error(f"Human tracking control error: {e}")
    
    def _handle_no_detection(self):
        """Handle case when no human is detected"""
        self.frames_since_detection += 1
        
        if self.frames_since_detection < 3:
            # Brief stop
            self.motor_controller.stop()
        elif self.frames_since_detection < self.max_frames_without_detection:
            # Light search
            self.motor_controller.move_with_turn(0, 20)
        else:
            # Complete stop
            self.motor_controller.stop()
            self.movement_history.clear()
    
    def _draw_visualization(self, frame, x, y, w, h, center_x, center_y, detection_time):
        """Draw visualization information"""
        # Bounding box
        cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
        
        # Center point
        cv2.circle(frame, (center_x, center_y), 5, (0, 255, 0), -1)
        
        # Target line
        cv2.line(frame, (self.target_x, 0), (self.target_x, self.frame_height), (255, 0, 0), 2)
        
        # Status information
        x_error = center_x - self.target_x
        distance_error = self.target_distance - h
        
        cv2.putText(frame, f"{self.detector_name} Tracking: X={x_error:+.0f} D={distance_error:+.0f}", 
                   (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
        cv2.putText(frame, f"Detection Time: {detection_time:.1f}ms | Size: {w}x{h}", 
                   (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)
    
    def stop_tracking(self):
        """Stop human tracking"""
        logger.info("Stopping ultra-lightweight human tracking...")
        self.tracking = False
        self.motor_controller.stop()
    
    def get_tracking_status(self) -> dict:
        """Get current tracking status"""
        with self.lock:
            return {
                'tracking': self.tracking,
                'detector_type': self.detector_name,
                'last_human_center': self.last_human_center,
                'target_center': (self.target_x, self.frame_height // 2),
                'frame_size': (self.frame_width, self.frame_height)
            }


class SimplePIDController:
    """Simplified PID controller"""
    
    def __init__(self, kp: float, ki: float, kd: float):
        self.kp = kp
        self.ki = ki
        self.kd = kd
        self.previous_error = 0
        self.integral = 0
        
    def update(self, error: float) -> float:
        # Proportional term
        p_term = self.kp * error
        
        # Integral term (prevent integral windup)
        self.integral += error
        self.integral = max(-50, min(50, self.integral))
        i_term = self.ki * self.integral
        
        # Derivative term
        derivative = error - self.previous_error
        d_term = self.kd * derivative
        
        self.previous_error = error
        
        return p_term + i_term + d_term
    
    def reset(self):
        self.previous_error = 0
        self.integral = 0