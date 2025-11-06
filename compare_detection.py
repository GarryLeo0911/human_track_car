#!/usr/bin/env python3
"""
Detection Performance Comparison Tool
Helps evaluate the accuracy improvements made to human detection.
"""

import time
import cv2
import numpy as np
import sys
import os

# Add src directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

def simple_hog_detector():
    """Original simple HOG detector for comparison."""
    hog = cv2.HOGDescriptor()
    detector = cv2.HOGDescriptor.getDefaultPeopleDetector()
    hog.setSVMDetector(np.array(detector, dtype=np.float32))
    
    def detect(frame):
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        # Simple detection without preprocessing
        boxes, weights = hog.detectMultiScale(gray, winStride=(8, 8), padding=(16, 16), scale=1.05)
        
        # Basic filtering
        confident_boxes = []
        for i, (x, y, w, h) in enumerate(boxes):
            if weights[i] > 0.3 and w > 40 and h > 80:
                confident_boxes.append((x, y, w, h))
        return confident_boxes
    
    return detect

def compare_detection_methods():
    """Compare old vs new detection methods."""
    
    print("Detection Method Comparison")
    print("=" * 40)
    print("This compares:")
    print("- Original HOG (left side)")
    print("- Improved HOG (right side)")
    print("Press 'q' to quit")
    print("")
    
    # Import improved detector
    from src.tracking.human_tracker import HumanDetector
    
    # Initialize detectors
    simple_detect = simple_hog_detector()
    improved_detector = HumanDetector()
    
    # Try to get camera
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Error: Could not open camera")
        return
    
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    
    # Statistics
    frame_count = 0
    simple_detections = 0
    improved_detections = 0
    simple_rate = 0.0
    improved_rate = 0.0
    
    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                continue
            
            frame_count += 1
            
            # Split frame for side-by-side comparison
            height, width = frame.shape[:2]
            left_frame = frame.copy()
            right_frame = frame.copy()
            
            # Test simple detector (left side)
            start_time = time.time()
            simple_boxes = simple_detect(frame)
            simple_time = (time.time() - start_time) * 1000
            
            if simple_boxes:
                simple_detections += 1
                for x, y, w, h in simple_boxes:
                    cv2.rectangle(left_frame, (x, y), (x + w, y + h), (0, 0, 255), 2)
                    cv2.putText(left_frame, "SIMPLE", (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
            
            # Test improved detector (right side)
            start_time = time.time()
            improved_boxes = improved_detector.detect_humans(frame)
            improved_time = (time.time() - start_time) * 1000
            
            if improved_boxes:
                improved_detections += 1
                for x, y, w, h in improved_boxes:
                    cv2.rectangle(right_frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
                    cv2.putText(right_frame, "IMPROVED", (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
            
            # Combine frames side by side
            combined = np.hstack([left_frame, right_frame])
            
            # Add statistics
            if frame_count > 0:
                simple_rate = (simple_detections / frame_count) * 100
                improved_rate = (improved_detections / frame_count) * 100
            
            # Add text overlay
            cv2.putText(combined, "ORIGINAL", (50, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
            cv2.putText(combined, f"{simple_rate:.1f}% | {simple_time:.1f}ms", (50, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)
            
            cv2.putText(combined, "IMPROVED", (width + 50, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
            cv2.putText(combined, f"{improved_rate:.1f}% | {improved_time:.1f}ms", (width + 50, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)
            
            # Separator line
            cv2.line(combined, (width, 0), (width, height), (255, 255, 255), 2)
            
            cv2.imshow('Detection Comparison', combined)
            
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
                
    except KeyboardInterrupt:
        pass
    finally:
        cap.release()
        cv2.destroyAllWindows()
        
        print(f"\nComparison Results (over {frame_count} frames):")
        print(f"Original detector: {simple_rate:.1f}% detection rate")
        print(f"Improved detector: {improved_rate:.1f}% detection rate")
        if frame_count > 0:
            improvement = improved_rate - simple_rate
            print(f"Improvement: {improvement:+.1f}%")

if __name__ == "__main__":
    compare_detection_methods()