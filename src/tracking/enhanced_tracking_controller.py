"""
Enhanced Target Tracking Controller
Based on learnings from ro-ken/target_follow project
Improved target selection, distance estimation, and smooth motion control
"""

import cv2
import numpy as np
import time
import logging
from typing import Tuple, List, Optional, Dict
from threading import Lock
import math

logger = logging.getLogger(__name__)

class EnhancedTrackingController:
    """
    Enhanced tracking controller with improved algorithms from target_follow project
    
    Key improvements:
    1. Distance estimation based on bounding box size
    2. Multi-target selection with historical tracking
    3. Smooth acceleration/deceleration control
    4. Better turning logic with proportional control
    5. Safety distance maintenance
    """
    
    def __init__(self, frame_width: int = 640, frame_height: int = 480):
        """Initialize enhanced tracking controller"""
        
        # Frame parameters
        self.frame_width = frame_width
        self.frame_height = frame_height
        self.center_x = frame_width // 2
        self.center_y = frame_height // 2
        
        # Target tracking parameters
        self.last_target_x = self.center_x
        self.last_target_y = self.center_y
        self.last_target_w = 0
        self.last_target_h = 0
        self.target_lost_count = 0
        self.max_lost_frames = 30  # Maximum frames to remember target
        
        # Distance estimation parameters (from target_follow)
        self.base_distance = 1.0  # Base distance in meters (when target fills reference width)
        self.base_width_ratio = 0.6  # Reference target width as ratio of frame width
        self.base_width_pixels = self.frame_width * self.base_width_ratio
        
        # Motion control parameters
        self.max_speed = 0.45  # Maximum forward speed
        self.back_speed = -0.15  # Backward speed
        self.max_turn_speed = 0.7  # Maximum turn speed
        self.time_interval = 0.4  # Time between frames (for velocity calculation)
        
        # Control thresholds (as ratios of frame width)
        self.turn_deadzone_left = 0.8   # Left turn threshold
        self.turn_deadzone_right = 1.2  # Right turn threshold
        self.turn_max_left = 0.2       # Maximum left turn threshold
        self.turn_max_right = 1.8      # Maximum right turn threshold
        
        # Distance control thresholds (as ratios of frame width)
        self.distance_too_close = 0.8   # Stop/backup threshold
        self.distance_optimal = 0.5     # Target distance threshold
        
        # Smooth control parameters
        self.speed_acceleration = 0.05  # Speed change per frame
        self.current_speed = 0.0
        self.current_turn = 0.0
        self.speed_smoothing = 0.7      # Speed smoothing factor
        self.turn_smoothing = 0.6       # Turn smoothing factor
        
        # Target selection parameters
        self.target_selection_threshold = 100  # Maximum pixel distance for target matching
        
        # Thread safety
        self.lock = Lock()
        
        logger.info("Enhanced tracking controller initialized")
    
    def update_target_tracking(self, detections: List[Tuple]) -> Dict:
        """
        Update tracking based on detections
        
        Args:
            detections: List of (x, y, w, h, confidence) tuples
            
        Returns:
            Control commands dictionary
        """
        with self.lock:
            if not detections:
                return self._handle_target_lost()
            
            # Select best target from detections
            selected_target = self._select_target(detections)
            
            if selected_target is None:
                return self._handle_target_lost()
            
            # Update target position
            x, y, w, h = selected_target[:4]
            confidence = selected_target[4] if len(selected_target) == 5 else 1.0
            
            # Calculate target center
            target_center_x = x + w // 2
            target_center_y = y + h // 2
            
            # Update tracking state
            self.last_target_x = target_center_x
            self.last_target_y = target_center_y
            self.last_target_w = w
            self.last_target_h = h
            self.target_lost_count = 0
            
            # Calculate control commands
            turn_command = self._calculate_turn_control(target_center_x)
            speed_command = self._calculate_speed_control(w)
            distance_estimate = self._estimate_distance(w)
            
            return {
                'speed': speed_command,
                'turn': turn_command,
                'target_x': target_center_x,
                'target_y': target_center_y,
                'target_width': w,
                'target_height': h,
                'distance_estimate': distance_estimate,
                'confidence': confidence,
                'tracking_status': 'active'
            }
    
    def _select_target(self, detections: List[Tuple]) -> Optional[Tuple]:
        """
        Select best target from multiple detections
        Based on target_follow's find_target_rect logic
        """
        if len(detections) == 1:
            return detections[0]
        
        if len(detections) == 0:
            return None
        
        # Find detection closest to last known target position
        min_distance = float('inf')
        best_target = None
        
        for detection in detections:
            x, y, w, h = detection[:4]
            center_x = x + w // 2
            center_y = y + h // 2
            
            # Calculate distance from last target position
            distance = math.sqrt(
                (center_x - self.last_target_x) ** 2 + 
                (center_y - self.last_target_y) ** 2
            )
            
            if distance < min_distance and distance < self.target_selection_threshold:
                min_distance = distance
                best_target = detection
        
        # If no target is close enough, select the largest one (most prominent)
        if best_target is None:
            best_target = max(detections, key=lambda det: det[2] * det[3])  # Largest area
        
        return best_target
    
    def _calculate_turn_control(self, target_x: int) -> float:
        """
        Calculate turn control based on target position
        Improved version of target_follow's tran_turn logic
        """
        # Normalize target position
        center_x_normalized = self.center_x
        left_threshold = center_x_normalized * self.turn_deadzone_left
        right_threshold = center_x_normalized * self.turn_deadzone_right
        
        if left_threshold <= target_x <= right_threshold:
            # Target is centered, no turning needed
            target_turn = 0.0
        elif target_x < left_threshold:
            # Turn left (target is to the left)
            turn_amount = (left_threshold - target_x) / center_x_normalized
            target_turn = min(turn_amount * self.max_turn_speed, self.max_turn_speed)
        else:
            # Turn right (target is to the right)
            turn_amount = (target_x - right_threshold) / center_x_normalized
            target_turn = -min(turn_amount * self.max_turn_speed, self.max_turn_speed)
        
        # Apply smoothing to reduce jerky movements
        self.current_turn = (
            self.turn_smoothing * self.current_turn + 
            (1 - self.turn_smoothing) * target_turn
        )
        
        return self.current_turn
    
    def _calculate_speed_control(self, target_width: int) -> float:
        """
        Calculate speed control based on target size (distance estimation)
        Based on target_follow's tran_speed logic
        """
        # Calculate distance and determine speed
        distance_ratio = target_width / self.frame_width
        
        # Distance control zones
        too_close_threshold = self.distance_too_close
        optimal_distance_threshold = self.distance_optimal
        
        if distance_ratio >= too_close_threshold:
            # Too close, move backward
            target_speed = self.back_speed
            
        elif distance_ratio <= optimal_distance_threshold:
            # Too far, move forward with calculated speed
            
            # Estimate required distance to travel
            estimated_distance = self.base_distance * (self.base_width_pixels / target_width) - self.base_distance
            required_speed = estimated_distance / self.time_interval
            
            # Apply gradual acceleration (from target_follow)
            if required_speed > self.current_speed:
                if self.current_speed < self.max_speed:
                    target_speed = min(self.current_speed + self.speed_acceleration, self.max_speed)
                else:
                    target_speed = required_speed
            else:
                target_speed = required_speed
                
            # Ensure minimum forward speed
            target_speed = max(target_speed, 0.2)
            
            # Reduce speed if target is at edge (partial view)
            if (self.last_target_x <= self.turn_max_left * self.center_x or 
                self.last_target_x >= self.turn_max_right * self.center_x):
                target_speed = min(target_speed, 0.2)
        
        else:
            # In optimal range, stop
            target_speed = 0.0
        
        # Apply smoothing
        self.current_speed = (
            self.speed_smoothing * self.current_speed + 
            (1 - self.speed_smoothing) * target_speed
        )
        
        return self.current_speed
    
    def _estimate_distance(self, target_width: int) -> float:
        """
        Estimate distance to target based on bounding box width
        Based on target_follow's distance estimation
        """
        if target_width <= 0:
            return float('inf')
        
        # Distance estimation: distance = base_distance * (base_width / current_width)
        estimated_distance = self.base_distance * (self.base_width_pixels / target_width)
        return max(0.1, estimated_distance)  # Minimum 10cm
    
    def _handle_target_lost(self) -> Dict:
        """Handle target lost situation"""
        self.target_lost_count += 1
        
        if self.target_lost_count < self.max_lost_frames:
            # Recently lost, maintain last known position
            status = 'tracking_lost_recent'
            # Gradually reduce speed
            self.current_speed *= 0.9
            self.current_turn *= 0.9
        else:
            # Lost for too long, stop all movement
            status = 'tracking_lost'
            self.current_speed = 0.0
            self.current_turn = 0.0
        
        return {
            'speed': self.current_speed,
            'turn': self.current_turn,
            'target_x': self.last_target_x,
            'target_y': self.last_target_y,
            'target_width': self.last_target_w,
            'target_height': self.last_target_h,
            'distance_estimate': float('inf'),
            'confidence': 0.0,
            'tracking_status': status,
            'lost_frames': self.target_lost_count
        }
    
    def get_tracking_info(self) -> Dict:
        """Get current tracking information"""
        with self.lock:
            return {
                'last_target_position': (self.last_target_x, self.last_target_y),
                'last_target_size': (self.last_target_w, self.last_target_h),
                'current_speed': self.current_speed,
                'current_turn': self.current_turn,
                'target_lost_count': self.target_lost_count,
                'distance_estimate': self._estimate_distance(self.last_target_w)
            }
    
    def reset_tracking(self):
        """Reset tracking state"""
        with self.lock:
            self.last_target_x = self.center_x
            self.last_target_y = self.center_y
            self.last_target_w = 0
            self.last_target_h = 0
            self.target_lost_count = 0
            self.current_speed = 0.0
            self.current_turn = 0.0
            logger.info("Tracking state reset")
    
    def configure_parameters(self, **kwargs):
        """Configure tracking parameters"""
        with self.lock:
            for key, value in kwargs.items():
                if hasattr(self, key):
                    setattr(self, key, value)
                    logger.info(f"Updated parameter {key} = {value}")
                else:
                    logger.warning(f"Unknown parameter: {key}")


class SmartTargetSelector:
    """
    Smart target selection with tracking history
    Improved version of target_follow's target selection
    """
    
    def __init__(self, max_history: int = 10):
        """Initialize target selector"""
        self.target_history = []
        self.max_history = max_history
        self.current_target_id = None
        
    def select_target(self, detections: List[Tuple], frame_center: Tuple[int, int]) -> Optional[Tuple]:
        """
        Select best target from detections with tracking continuity
        
        Args:
            detections: List of detection tuples
            frame_center: (center_x, center_y) of frame
            
        Returns:
            Selected target tuple or None
        """
        if not detections:
            return None
        
        if len(detections) == 1:
            target = detections[0]
            self._update_history(target)
            return target
        
        # Multiple targets - need intelligent selection
        if self.target_history:
            # Try to maintain tracking continuity
            best_target = self._find_continuous_target(detections)
            if best_target:
                self._update_history(best_target)
                return best_target
        
        # No history or no matching target - select best one
        best_target = self._select_best_new_target(detections, frame_center)
        self._update_history(best_target)
        return best_target
    
    def _find_continuous_target(self, detections: List[Tuple]) -> Optional[Tuple]:
        """Find target that continues previous tracking"""
        if not self.target_history:
            return None
        
        last_target = self.target_history[-1]
        last_x = last_target[0] + last_target[2] // 2
        last_y = last_target[1] + last_target[3] // 2
        
        min_distance = float('inf')
        best_match = None
        
        for detection in detections:
            x, y, w, h = detection[:4]
            center_x = x + w // 2
            center_y = y + h // 2
            
            distance = math.sqrt((center_x - last_x)**2 + (center_y - last_y)**2)
            
            if distance < min_distance and distance < 150:  # Maximum tracking distance
                min_distance = distance
                best_match = detection
        
        return best_match
    
    def _select_best_new_target(self, detections: List[Tuple], frame_center: Tuple[int, int]) -> Tuple:
        """Select best new target when no tracking continuity"""
        center_x, center_y = frame_center
        
        # Prioritize targets closer to center and larger in size
        def target_score(detection):
            x, y, w, h = detection[:4]
            target_center_x = x + w // 2
            target_center_y = y + h // 2
            
            # Distance from center (normalized)
            distance_from_center = math.sqrt(
                (target_center_x - center_x)**2 + (target_center_y - center_y)**2
            )
            center_score = 1.0 / (1.0 + distance_from_center / 100)
            
            # Size score (larger is better)
            area = w * h
            size_score = area / (frame_center[0] * frame_center[1])  # Normalized by frame area
            
            # Confidence score if available
            confidence = detection[4] if len(detection) == 5 else 1.0
            
            return center_score * 0.4 + size_score * 0.4 + confidence * 0.2
        
        return max(detections, key=target_score)
    
    def _update_history(self, target: Tuple):
        """Update target tracking history"""
        self.target_history.append(target)
        if len(self.target_history) > self.max_history:
            self.target_history.pop(0)
    
    def reset_history(self):
        """Reset tracking history"""
        self.target_history.clear()
        self.current_target_id = None