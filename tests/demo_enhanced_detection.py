#!/usr/bin/env python3
"""
Enhanced Detection Demo Script
Quick demo of improved human detection accuracy
"""

import cv2
import time
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

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def demo_enhanced_detection():
    """Demo the enhanced detection capabilities"""
    print("Enhanced Human Detection Demo")
    print("=============================")
    print("This demo shows improved human detection accuracy")
    print("Press 'q' to quit, 'c' to cycle through detectors")
    print()
    
    # Initialize detectors
    detectors = [
        ("Enhanced Motion Detection", EnhancedMotionDetector()),
        ("Enhanced Edge Detection", EnhancedEdgeDetector()),
        ("Hybrid Detection (Best)", HybridHumanDetector())
    ]
    
    current_detector_idx = 0
    detector_name, detector = detectors[current_detector_idx]
    
    # Initialize camera
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Error: Cannot open camera")
        return
    
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    
    print(f"Starting with: {detector_name}")
    
    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            # Perform detection
            start_time = time.time()
            detections = detector.detect_humans(frame)
            detection_time = (time.time() - start_time) * 1000
            
            # Draw results
            result_frame = frame.copy()
            
            # Draw detection boxes
            for detection in detections:
                if len(detection) >= 4:
                    x, y, w, h = detection[:4]
                    confidence = detection[4] if len(detection) == 5 else 0.0
                    
                    # Color based on confidence
                    if confidence > 0.8:
                        color = (0, 255, 0)  # Green - High confidence
                    elif confidence > 0.6:
                        color = (0, 255, 255)  # Yellow - Medium confidence
                    else:
                        color = (0, 0, 255)  # Red - Low confidence
                    
                    # Draw bounding box
                    cv2.rectangle(result_frame, (x, y), (x + w, y + h), color, 2)
                    
                    # Draw confidence score
                    if confidence > 0:
                        cv2.putText(result_frame, f'{confidence:.2f}', 
                                  (x, y - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
                    
                    # Draw center point
                    center_x, center_y = x + w // 2, y + h // 2
                    cv2.circle(result_frame, (center_x, center_y), 5, color, -1)
            
            # Draw information overlay
            info_y = 30
            cv2.putText(result_frame, f"Detector: {detector_name}", 
                       (10, info_y), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            
            info_y += 25
            cv2.putText(result_frame, f"Detections: {len(detections)}", 
                       (10, info_y), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
            
            info_y += 25
            cv2.putText(result_frame, f"Time: {detection_time:.1f}ms", 
                       (10, info_y), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
            
            # Draw instructions
            cv2.putText(result_frame, "Press 'c' to cycle detectors, 'q' to quit", 
                       (10, frame.shape[0] - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
            
            # Show result
            cv2.imshow('Enhanced Human Detection Demo', result_frame)
            
            # Handle key press
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                break
            elif key == ord('c'):
                # Cycle to next detector
                current_detector_idx = (current_detector_idx + 1) % len(detectors)
                detector_name, detector = detectors[current_detector_idx]
                print(f"Switched to: {detector_name}")
    
    finally:
        cap.release()
        cv2.destroyAllWindows()
        print("Demo completed!")

def quick_performance_test():
    """Quick performance comparison"""
    print("\nQuick Performance Test")
    print("======================")
    
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Camera not available for performance test")
        return
    
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    
    # Get a test frame
    ret, frame = cap.read()
    cap.release()
    
    if not ret:
        print("Cannot capture test frame")
        return
    
    # Test detectors
    detectors = [
        ("Enhanced Motion", EnhancedMotionDetector()),
        ("Enhanced Edge", EnhancedEdgeDetector()),
        ("Hybrid Detection", HybridHumanDetector())
    ]
    
    for name, detector in detectors:
        # Warm up
        for _ in range(3):
            detector.detect_humans(frame)
        
        # Measure performance
        times = []
        detection_counts = []
        
        for _ in range(10):
            start_time = time.time()
            detections = detector.detect_humans(frame)
            detection_time = (time.time() - start_time) * 1000
            
            times.append(detection_time)
            detection_counts.append(len(detections))
        
        avg_time = sum(times) / len(times)
        avg_detections = sum(detection_counts) / len(detection_counts)
        
        print(f"{name:20}: {avg_time:6.1f}ms avg, {avg_detections:.1f} detections avg")

def main():
    """Main demo function"""
    print("Enhanced Human Detection System")
    print("===============================")
    print("Features:")
    print("- Multi-frame validation for stability")
    print("- Confidence scoring for each detection")
    print("- Human shape and proportion analysis")
    print("- Advanced background subtraction")
    print("- Hybrid detection combining multiple methods")
    print()
    
    while True:
        print("Choose demo mode:")
        print("1. Interactive detection demo")
        print("2. Quick performance test")
        print("3. Exit")
        
        choice = input("Enter choice (1-3): ").strip()
        
        if choice == '1':
            demo_enhanced_detection()
        elif choice == '2':
            quick_performance_test()
        elif choice == '3':
            break
        else:
            print("Invalid choice")
    
    print("Demo finished!")

if __name__ == "__main__":
    main()