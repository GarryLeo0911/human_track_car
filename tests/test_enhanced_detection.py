#!/usr/bin/env python3
"""
Enhanced Human Detection Testing Script
Test and compare the accuracy of different detection methods
"""

import cv2
import time
import numpy as np
import logging
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.tracking.enhanced_human_detector import (
    HybridHumanDetector, 
    EnhancedMotionDetector, 
    EnhancedEdgeDetector
)
from src.tracking.ultra_light_tracker import (
    MotionBasedDetector,
    EdgeBasedDetector,
    ColorBasedDetector
)

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DetectionComparison:
    """Compare different detection methods"""
    
    def __init__(self):
        """Initialize all detectors"""
        print("Initializing detectors...")
        
        # Enhanced detectors
        self.enhanced_motion = EnhancedMotionDetector()
        self.enhanced_edge = EnhancedEdgeDetector()
        self.hybrid = HybridHumanDetector()
        
        # Basic detectors
        self.basic_motion = MotionBasedDetector()
        self.basic_edge = EdgeBasedDetector()
        self.color = ColorBasedDetector()
        
        # Detector list with names
        self.detectors = [
            ("Basic Motion", self.basic_motion),
            ("Enhanced Motion", self.enhanced_motion),
            ("Basic Edge", self.basic_edge),
            ("Enhanced Edge", self.enhanced_edge),
            ("Color Detection", self.color),
            ("Hybrid (Motion+Edge)", self.hybrid)
        ]
        
        # Performance tracking
        self.performance_stats = {}
        for name, _ in self.detectors:
            self.performance_stats[name] = {
                'detection_times': [],
                'detection_counts': [],
                'confidence_scores': []
            }
    
    def test_camera_detection(self, duration_seconds=30):
        """Test detection using camera feed"""
        print(f"Starting camera detection test for {duration_seconds} seconds...")
        print("Press 'q' to quit early, 's' to save current frame")
        
        # Initialize camera
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            print("Error: Cannot open camera")
            return
        
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        
        start_time = time.time()
        frame_count = 0
        
        try:
            while True:
                ret, frame = cap.read()
                if not ret:
                    print("Error: Cannot read frame")
                    break
                
                frame_count += 1
                current_time = time.time()
                
                # Check if test duration exceeded
                if current_time - start_time > duration_seconds:
                    break
                
                # Test all detectors
                detection_results = self._test_frame(frame)
                
                # Create visualization
                display_frame = self._create_comparison_visualization(frame, detection_results)
                
                # Show results
                cv2.imshow('Enhanced Detection Comparison', display_frame)
                
                # Handle key press
                key = cv2.waitKey(1) & 0xFF
                if key == ord('q'):
                    break
                elif key == ord('s'):
                    # Save current frame with detections
                    timestamp = int(time.time())
                    cv2.imwrite(f'detection_comparison_{timestamp}.jpg', display_frame)
                    print(f"Saved frame: detection_comparison_{timestamp}.jpg")
                
                # Print progress every 5 seconds
                if frame_count % 150 == 0:  # Assuming ~30 FPS
                    elapsed = current_time - start_time
                    print(f"Progress: {elapsed:.1f}s / {duration_seconds}s")
        
        finally:
            cap.release()
            cv2.destroyAllWindows()
        
        # Print final statistics
        self._print_performance_summary()
    
    def _test_frame(self, frame):
        """Test all detectors on a single frame"""
        results = {}
        
        for detector_name, detector in self.detectors:
            start_time = time.time()
            
            try:
                detections = detector.detect_humans(frame)
                detection_time = (time.time() - start_time) * 1000  # Convert to ms
                
                # Store performance data
                self.performance_stats[detector_name]['detection_times'].append(detection_time)
                self.performance_stats[detector_name]['detection_counts'].append(len(detections))
                
                # Store confidence scores if available
                if detections and len(detections[0]) == 5:  # Has confidence
                    confidences = [det[4] for det in detections]
                    self.performance_stats[detector_name]['confidence_scores'].extend(confidences)
                
                results[detector_name] = {
                    'detections': detections,
                    'time': detection_time,
                    'count': len(detections)
                }
                
            except Exception as e:
                logger.error(f"Error in {detector_name}: {e}")
                results[detector_name] = {
                    'detections': [],
                    'time': 0,
                    'count': 0,
                    'error': str(e)
                }
        
        return results
    
    def _create_comparison_visualization(self, frame, results):
        """Create a visualization comparing all detection results"""
        height, width = frame.shape[:2]
        
        # Create a larger canvas for comparison
        canvas_width = width * 3
        canvas_height = height * 2
        canvas = np.zeros((canvas_height, canvas_width, 3), dtype=np.uint8)
        
        # Color scheme for different detectors
        colors = [
            (0, 255, 0),      # Basic Motion - Green
            (0, 255, 255),    # Enhanced Motion - Yellow
            (255, 0, 0),      # Basic Edge - Blue
            (255, 0, 255),    # Enhanced Edge - Magenta
            (0, 165, 255),    # Color - Orange
            (255, 255, 255)   # Hybrid - White
        ]
        
        # Position frames
        positions = [
            (0, 0),                    # Top-left
            (width, 0),               # Top-center
            (width * 2, 0),           # Top-right
            (0, height),              # Bottom-left
            (width, height),          # Bottom-center
            (width * 2, height)       # Bottom-right
        ]
        
        for i, ((detector_name, _), (x, y)) in enumerate(zip(self.detectors, positions)):
            # Copy original frame to position
            canvas[y:y+height, x:x+width] = frame.copy()
            
            # Draw detections
            if detector_name in results:
                result = results[detector_name]
                detections = result['detections']
                detection_time = result['time']
                
                # Draw bounding boxes
                for detection in detections:
                    if len(detection) >= 4:
                        dx, dy, dw, dh = detection[:4]
                        confidence = detection[4] if len(detection) == 5 else 0.0
                        
                        # Draw rectangle
                        cv2.rectangle(canvas, 
                                    (x + dx, y + dy), 
                                    (x + dx + dw, y + dy + dh), 
                                    colors[i], 2)
                        
                        # Draw confidence if available
                        if confidence > 0:
                            cv2.putText(canvas, f'{confidence:.2f}', 
                                      (x + dx, y + dy - 5), 
                                      cv2.FONT_HERSHEY_SIMPLEX, 0.5, colors[i], 1)
                
                # Draw detector info
                info_text = f"{detector_name}: {len(detections)} det, {detection_time:.1f}ms"
                cv2.putText(canvas, info_text, 
                          (x + 5, y + 25), 
                          cv2.FONT_HERSHEY_SIMPLEX, 0.6, colors[i], 2)
                
                # Draw error if any
                if 'error' in result:
                    cv2.putText(canvas, f"ERROR: {result['error'][:30]}", 
                              (x + 5, y + 50), 
                              cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)
        
        return canvas
    
    def _print_performance_summary(self):
        """Print performance summary statistics"""
        print("\n" + "="*80)
        print("DETECTION PERFORMANCE SUMMARY")
        print("="*80)
        
        for detector_name in self.performance_stats:
            stats = self.performance_stats[detector_name]
            
            if not stats['detection_times']:
                continue
            
            avg_time = np.mean(stats['detection_times'])
            avg_detections = np.mean(stats['detection_counts'])
            
            print(f"\n{detector_name}:")
            print(f"  Average detection time: {avg_time:.2f}ms")
            print(f"  Average detections per frame: {avg_detections:.2f}")
            
            if stats['confidence_scores']:
                avg_confidence = np.mean(stats['confidence_scores'])
                print(f"  Average confidence score: {avg_confidence:.3f}")
            
            # Performance rating
            if avg_time < 20:
                speed_rating = "Excellent"
            elif avg_time < 40:
                speed_rating = "Good"
            elif avg_time < 60:
                speed_rating = "Fair"
            else:
                speed_rating = "Slow"
            
            print(f"  Speed rating: {speed_rating}")
        
        print("\n" + "="*80)
    
    def test_static_image(self, image_path):
        """Test detection on a static image"""
        print(f"Testing detection on image: {image_path}")
        
        # Load image
        frame = cv2.imread(image_path)
        if frame is None:
            print(f"Error: Cannot load image {image_path}")
            return
        
        # Test all detectors
        results = self._test_frame(frame)
        
        # Create visualization
        display_frame = self._create_comparison_visualization(frame, results)
        
        # Save result
        output_path = f"detection_test_{int(time.time())}.jpg"
        cv2.imwrite(output_path, display_frame)
        print(f"Saved comparison result: {output_path}")
        
        # Show result
        cv2.imshow('Detection Comparison', display_frame)
        cv2.waitKey(0)
        cv2.destroyAllWindows()


def main():
    """Main testing function"""
    print("Enhanced Human Detection Testing")
    print("================================")
    
    comparison = DetectionComparison()
    
    while True:
        print("\nSelect test mode:")
        print("1. Camera detection test (30 seconds)")
        print("2. Camera detection test (custom duration)")
        print("3. Static image test")
        print("4. Quick camera test (10 seconds)")
        print("5. Exit")
        
        choice = input("Enter choice (1-5): ").strip()
        
        if choice == '1':
            comparison.test_camera_detection(30)
        elif choice == '2':
            try:
                duration = int(input("Enter test duration in seconds: "))
                comparison.test_camera_detection(duration)
            except ValueError:
                print("Invalid duration")
        elif choice == '3':
            image_path = input("Enter image path: ").strip()
            comparison.test_static_image(image_path)
        elif choice == '4':
            comparison.test_camera_detection(10)
        elif choice == '5':
            break
        else:
            print("Invalid choice")
    
    print("Testing completed!")


if __name__ == "__main__":
    main()