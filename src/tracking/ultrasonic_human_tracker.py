"""
Enhanced Human Tracker with Ultrasonic Distance Support
Combines computer vision with ultrasonic distance measurements for improved tracking.
"""

import cv2
import numpy as np
import logging
import time
from threading import Lock
from typing import Tuple, Optional, List

from .human_tracker import HumanTracker, HumanDetector, PIDController
from ..sensors.ultrasonic_sensor import UltrasonicSensor

logger = logging.getLogger(__name__)


class UltrasonicHumanTracker(HumanTracker):
    """
    Enhanced human tracker that combines vision tracking with ultrasonic distance sensing.
    Based on Freenove official ultrasonic implementation.
    """
    
    def __init__(self, camera_manager, motor_controller, use_ultrasonic: bool = True):
        """
        Initialize the enhanced tracker.
        
        Args:
            camera_manager: Camera management instance
            motor_controller: Motor control instance  
            use_ultrasonic: Whether to use ultrasonic sensor (default: True)
        """
        # Initialize base tracker
        super().__init__(camera_manager, motor_controller)
        
        # Ultrasonic sensor setup
        self.use_ultrasonic = use_ultrasonic
        self.ultrasonic = None
        
        if self.use_ultrasonic:
            try:
                self.ultrasonic = UltrasonicSensor()
                logger.info("Ultrasonic sensor initialized for enhanced tracking")
            except Exception as e:
                logger.error(f"Failed to initialize ultrasonic sensor: {e}")
                self.use_ultrasonic = False
        
        # Enhanced tracking parameters
        self.target_distance_cm = 80      # Target distance in centimeters (from ultrasonic)
        self.distance_tolerance = 15      # ±15cm tolerance
        self.min_tracking_distance = 30   # Minimum distance to track (30cm)
        self.max_tracking_distance = 200  # Maximum distance to track (2m)
        
        # Distance-based PID controller (separate from vision-based)
        self.pid_ultrasonic_distance = PIDController(kp=0.8, ki=0.1, kd=0.2)
        
        # Sensor fusion parameters
        self.vision_weight = 0.6          # Weight for vision-based distance
        self.ultrasonic_weight = 0.4      # Weight for ultrasonic distance
        self.use_sensor_fusion = True     # Combine both sensors
        
        # Distance tracking
        self.last_ultrasonic_distance = None
        self.distance_history = []
        self.distance_history_length = 5
        
        # Enhanced status tracking
        self.tracking_mode = "vision_only"  # "vision_only", "ultrasonic_only", "sensor_fusion"
    
    def start_enhanced_tracking(self):
        """Start enhanced tracking with ultrasonic support."""
        logger.info("Starting enhanced human tracking with ultrasonic support...")
        
        # Start ultrasonic monitoring if available
        if self.ultrasonic:
            self.ultrasonic.start_continuous_monitoring()
            self.tracking_mode = "sensor_fusion"
        else:
            self.tracking_mode = "vision_only"
        
        # Call parent start_tracking
        super().start_tracking()
    
    def stop_tracking(self):
        """Stop enhanced tracking."""
        logger.info("Stopping enhanced human tracking...")
        
        # Stop ultrasonic monitoring
        if self.ultrasonic:
            self.ultrasonic.stop_continuous_monitoring()
        
        # Call parent stop_tracking
        super().stop_tracking()
    
    def _get_ultrasonic_distance(self) -> Optional[float]:
        """Get current ultrasonic distance measurement."""
        if not self.ultrasonic:
            return None
        
        distance = self.ultrasonic.get_smoothed_distance()
        
        if distance is not None:
            # Update distance history
            self.distance_history.append(distance)
            if len(self.distance_history) > self.distance_history_length:
                self.distance_history.pop(0)
            
            self.last_ultrasonic_distance = distance
        
        return distance
    
    def _estimate_vision_distance(self, human_height: int) -> float:
        """
        Estimate distance from human height in pixels (vision-based).
        This is a rough calibration - you may need to adjust based on your camera.
        
        Args:
            human_height: Height of detected human in pixels
            
        Returns:
            Estimated distance in centimeters
        """
        # Rough calibration: larger person in image = closer distance
        # This is very approximate and should be calibrated for your setup
        if human_height > 200:
            return 60  # Very close
        elif human_height > 150:
            return 80  # Target distance
        elif human_height > 100:
            return 120  # Somewhat far
        elif human_height > 60:
            return 160  # Far
        else:
            return 200  # Very far
    
    def _fuse_distance_measurements(self, vision_distance: float, ultrasonic_distance: Optional[float]) -> float:
        """
        Combine vision and ultrasonic distance measurements.
        
        Args:
            vision_distance: Distance estimated from vision (cm)
            ultrasonic_distance: Distance from ultrasonic sensor (cm)
            
        Returns:
            Fused distance measurement (cm)
        """
        if ultrasonic_distance is None or not self.use_sensor_fusion:
            return vision_distance
        
        # Weighted average of both measurements
        fused_distance = (self.vision_weight * vision_distance + 
                         self.ultrasonic_weight * ultrasonic_distance)
        
        logger.debug(f"Distance fusion: vision={vision_distance:.1f}cm, "
                    f"ultrasonic={ultrasonic_distance:.1f}cm, "
                    f"fused={fused_distance:.1f}cm")
        
        return fused_distance
    
    def _track_human_enhanced(self, center_x: int, human_height: int):
        """
        Enhanced tracking that combines vision and ultrasonic data.
        
        Args:
            center_x: X coordinate of human center
            human_height: Height of detected human in pixels
        """
        try:
            # Reset frames counter since we have detection
            self.frames_since_detection = 0
            self.last_valid_center = center_x
            
            # Get ultrasonic distance
            ultrasonic_distance = self._get_ultrasonic_distance()
            
            # Calculate errors for X-axis (vision-based)
            x_error = center_x - self.target_x
            
            # Calculate distance error using enhanced method
            if ultrasonic_distance is not None and self.use_ultrasonic:
                # Use ultrasonic distance as primary distance measurement
                distance_error_cm = self.target_distance_cm - ultrasonic_distance
                
                # Also get vision-based distance for comparison
                vision_distance = self._estimate_vision_distance(human_height)
                fused_distance = self._fuse_distance_measurements(vision_distance, ultrasonic_distance)
                distance_error_cm = self.target_distance_cm - fused_distance
                
                self.tracking_mode = "sensor_fusion"
            else:
                # Fall back to vision-only distance estimation
                vision_distance = self._estimate_vision_distance(human_height)
                distance_error_cm = self.target_distance_cm - vision_distance
                
                self.tracking_mode = "vision_only"
            
            # Edge detection for turning
            is_at_edge = center_x < self.edge_threshold or center_x > (self.frame_width - self.edge_threshold)
            
            # Calculate control outputs
            turn_output = self.pid_x.update(x_error)
            
            # Use ultrasonic-specific PID for distance if available
            if self.tracking_mode == "sensor_fusion":
                speed_output = self.pid_ultrasonic_distance.update(distance_error_cm)
                # Convert from cm to speed (scale factor)
                speed_output = speed_output * 2  # Adjust scale factor as needed
            else:
                # Use original vision-based distance control
                vision_distance_error = self.target_distance - human_height
                speed_output = self.pid_distance.update(vision_distance_error)
            
            # Apply adaptive scaling
            if is_at_edge:
                turn_scale = 0.7
                speed_scale = 0.8
            else:
                turn_scale = 1.0
                speed_scale = 1.0
            
            # Calculate final motor commands
            forward_speed = max(-self.max_forward_speed, min(self.max_forward_speed, speed_output * speed_scale))
            turn_speed = max(-self.max_turn_speed, min(self.max_turn_speed, turn_output * turn_scale))
            
            # Enhanced deadzones
            x_deadzone = 25 if is_at_edge else 20
            
            # Distance deadzone in cm for ultrasonic
            if self.tracking_mode == "sensor_fusion":
                distance_deadzone = self.distance_tolerance
                if abs(distance_error_cm) < distance_deadzone:
                    forward_speed = 0
            else:
                distance_deadzone = 15
                if abs(self.target_distance - human_height) < distance_deadzone:
                    forward_speed = 0
            
            if abs(x_error) < x_deadzone:
                turn_speed = 0
            
            # Safety check: stop if too close (ultrasonic safety)
            if ultrasonic_distance is not None and ultrasonic_distance < self.min_tracking_distance:
                forward_speed = min(0, forward_speed)  # Only allow backward movement
                logger.warning(f"Too close! Distance: {ultrasonic_distance:.1f}cm")
            
            # Send commands to motor controller
            self.motor_controller.move_with_turn(forward_speed, turn_speed)
            
            # Enhanced logging
            if ultrasonic_distance is not None:
                logger.info(f"ENHANCED_TRACK [{self.tracking_mode}]: "
                           f"x_err={x_error:+3.0f}, dist_err={distance_error_cm:+3.0f}cm, "
                           f"ultrasonic={ultrasonic_distance:.1f}cm, "
                           f"turn={turn_speed:+3.0f}, speed={forward_speed:+3.0f}")
            else:
                logger.info(f"VISION_TRACK: x_err={x_error:+3.0f}, "
                           f"turn={turn_speed:+3.0f}, speed={forward_speed:+3.0f}")
                           
        except Exception as e:
            logger.error(f"Error in enhanced human tracking: {e}")
    
    def _track_human(self, center_x: int, human_height: int):
        """Override parent method to use enhanced tracking."""
        self._track_human_enhanced(center_x, human_height)
    
    def _add_ultrasonic_visualization(self, frame: np.ndarray):
        """Add ultrasonic sensor information to video frame."""
        if not self.ultrasonic:
            return
        
        distance = self._get_ultrasonic_distance()
        
        if distance is not None:
            # Distance display
            color = (0, 255, 0)  # Green
            if distance < self.min_tracking_distance:
                color = (0, 0, 255)  # Red - too close
            elif distance > self.max_tracking_distance:
                color = (255, 0, 0)  # Blue - too far
            elif abs(distance - self.target_distance_cm) > self.distance_tolerance:
                color = (0, 255, 255)  # Yellow - adjusting
            
            cv2.putText(frame, f"Distance: {distance:.1f}cm", 
                       (10, frame.shape[0] - 60), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
            cv2.putText(frame, f"Target: {self.target_distance_cm}cm", 
                       (10, frame.shape[0] - 40), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
            cv2.putText(frame, f"Mode: {self.tracking_mode}", 
                       (10, frame.shape[0] - 20), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
            
            # Distance bar visualization
            bar_width = 200
            bar_height = 20
            bar_x = frame.shape[1] - bar_width - 10
            bar_y = frame.shape[0] - 40
            
            # Background bar
            cv2.rectangle(frame, (bar_x, bar_y), (bar_x + bar_width, bar_y + bar_height), (50, 50, 50), -1)
            
            # Distance indicator
            if distance <= self.max_tracking_distance:
                fill_width = int((distance / self.max_tracking_distance) * bar_width)
                cv2.rectangle(frame, (bar_x, bar_y), (bar_x + fill_width, bar_y + bar_height), color, -1)
            
            # Target marker
            target_pos = int((self.target_distance_cm / self.max_tracking_distance) * bar_width)
            cv2.line(frame, (bar_x + target_pos, bar_y - 5), (bar_x + target_pos, bar_y + bar_height + 5), (255, 255, 255), 2)
    
    def start_tracking(self):
        """Enhanced start_tracking with ultrasonic visualization."""
        logger.info("Starting enhanced human tracking with ultrasonic support...")
        self.tracking = True
        
        # Start ultrasonic monitoring if available
        if self.ultrasonic:
            self.ultrasonic.start_continuous_monitoring()
            self.tracking_mode = "sensor_fusion"
        else:
            self.tracking_mode = "vision_only"
        
        # Reset controllers and state
        self.pid_x.reset()
        self.pid_distance.reset()
        if hasattr(self, 'pid_ultrasonic_distance'):
            self.pid_ultrasonic_distance.reset()
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
                
                # Detect humans
                human_boxes = self.detector.detect_humans(frame)
                
                if human_boxes:
                    # Track detection confidence
                    self.recent_detections.append(True)
                    if len(self.recent_detections) > self.detection_history_length:
                        self.recent_detections.pop(0)
                    
                    # Select largest detection
                    largest_box = max(human_boxes, key=lambda box: box[2] * box[3])
                    x, y, w, h = largest_box
                    
                    # Calculate center
                    center_x = x + w // 2
                    center_y = y + h // 2
                    human_height = h
                    
                    # Update last known position
                    with self.lock:
                        self.last_human_center = (center_x, center_y, human_height)
                    
                    # Use enhanced tracking
                    self._track_human_enhanced(center_x, human_height)
                    
                    # Simplified visualization
                    cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
                    cv2.circle(frame, (center_x, center_y), 5, (0, 0, 255), -1)
                    cv2.line(frame, (self.target_x, 0), (self.target_x, self.frame_height), (255, 0, 0), 1)
                    
                    # Enhanced status with distance info
                    x_error = center_x - self.target_x
                    cv2.putText(frame, f"ENHANCED TRACK: X={x_error:+.0f}", (10, 30), 
                               cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
                    
                    # Add ultrasonic visualization
                    self._add_ultrasonic_visualization(frame)
                    
                else:
                    # Handle no detection
                    self.recent_detections.append(False)
                    if len(self.recent_detections) > self.detection_history_length:
                        self.recent_detections.pop(0)
                    
                    recent_detection_rate = sum(self.recent_detections) / len(self.recent_detections)
                    
                    if recent_detection_rate < 0.3:
                        self._handle_no_detection()
                    else:
                        if self.frames_since_detection < 2:
                            pass
                        else:
                            self.motor_controller.stop()
                    
                    with self.lock:
                        self.last_human_center = None
                    
                    detection_pct = int(recent_detection_rate * 100)
                    cv2.putText(frame, f"DETECTION: {detection_pct}% ({self.frames_since_detection})", 
                               (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
                    
                    # Still show ultrasonic info when searching
                    self._add_ultrasonic_visualization(frame)
                
                # Update camera manager with processed frame
                self.camera_manager.set_processed_frame(frame)
                
            except Exception as e:
                logger.error(f"Error in enhanced tracking loop: {e}")
    
    def get_enhanced_status(self) -> dict:
        """Get enhanced tracking status including ultrasonic data."""
        base_status = super().get_tracking_status()
        
        ultrasonic_status = {}
        if self.ultrasonic:
            ultrasonic_status = self.ultrasonic.get_status()
        
        return {
            **base_status,
            'tracking_mode': self.tracking_mode,
            'use_ultrasonic': self.use_ultrasonic,
            'target_distance_cm': self.target_distance_cm,
            'last_ultrasonic_distance': self.last_ultrasonic_distance,
            'ultrasonic_sensor': ultrasonic_status
        }
    
    def cleanup(self):
        """Cleanup enhanced tracker resources."""
        self.stop_tracking()
        if self.ultrasonic:
            self.ultrasonic.close()
        logger.info("Enhanced human tracker cleaned up")


# Test the enhanced tracker
if __name__ == '__main__':
    print("Testing Enhanced Human Tracker with Ultrasonic")
    print("This would require camera and motor controllers in real use")
    print("=" * 60)
    
    # Simulate testing
    ultrasonic = UltrasonicSensor()
    
    try:
        ultrasonic.start_continuous_monitoring()
        print("Ultrasonic sensor monitoring...")
        
        for i in range(10):
            distance = ultrasonic.get_smoothed_distance()
            stats = ultrasonic.get_distance_stats()
            
            print(f"Reading {i+1}: {distance:.1f}cm (avg: {stats['average']:.1f}cm)")
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\nTest interrupted")
    finally:
        ultrasonic.close()
        print("Test completed")