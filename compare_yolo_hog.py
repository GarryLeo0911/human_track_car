#!/usr/bin/env python3
"""
YOLO vs HOG Detection Comparison
Visual comparison tool to demonstrate accuracy improvements with YOLOv8n
"""

import cv2
import numpy as np
import time
import sys
import os
from concurrent.futures import ThreadPoolExecutor

# Add src directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

def hog_detector():
    """Create simple HOG detector for comparison."""
    hog = cv2.HOGDescriptor()
    detector = cv2.HOGDescriptor.getDefaultPeopleDetector()
    hog.setSVMDetector(np.array(detector, dtype=np.float32))
    
    def detect(frame):
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        boxes, weights = hog.detectMultiScale(gray, winStride=(8, 8), padding=(16, 16), scale=1.05)
        
        detections = []
        for i, (x, y, w, h) in enumerate(boxes):
            if weights[i] > 0.3 and w > 40 and h > 80:
                detections.append((x, y, w, h, float(weights[i])))
        return detections
    
    return detect

def yolo_detector():
    """Create YOLO detector for comparison."""
    try:
        from ultralytics import YOLO
        model = YOLO('yolov8n.pt')
        model.overrides['verbose'] = False
        
        def detect(frame):
            results = model(frame, conf=0.5, classes=[0], verbose=False)
            detections = []
            
            if results and len(results) > 0:
                result = results[0]
                if result.boxes is not None:
                    boxes = result.boxes.xyxy.cpu().numpy()
                    confidences = result.boxes.conf.cpu().numpy()
                    
                    for box, conf in zip(boxes, confidences):
                        x1, y1, x2, y2 = box.astype(int)
                        x, y, w, h = x1, y1, x2 - x1, y2 - y1
                        
                        # Validate detection
                        if w > 20 and h > 40 and 1.2 <= h/w <= 5.0:
                            detections.append((x, y, w, h, float(conf)))
            
            return detections
        
        return detect
    except ImportError:
        return None

def run_detection_comparison():
    """Run side-by-side detection comparison."""
    
    print("YOLO vs HOG Detection Comparison")
    print("=" * 50)
    
    # Initialize detectors
    hog_detect = hog_detector()
    yolo_detect = yolo_detector()
    
    if yolo_detect is None:
        print("YOLOv8 not available. Install with:")
        print("pip install ultralytics torch torchvision")
        return
    
    # Initialize camera
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Could not open camera")
        return
    
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    
    print("Starting comparison...")
    print("Left side: HOG Detector (traditional)")
    print("Right side: YOLOv8n Detector (modern)")
    print("Press 'q' to quit, 's' to save comparison image")
    
    # Statistics
    frame_count = 0
    hog_stats = {'detections': 0, 'time': []}
    yolo_stats = {'detections': 0, 'time': []}
    hog_rate = 0.0
    yolo_rate = 0.0
    hog_avg_time = 0.0
    yolo_avg_time = 0.0
    improvement = 0.0
    
    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                continue
            
            frame_count += 1
            height, width = frame.shape[:2]
            
            # Create side-by-side frames
            left_frame = frame.copy()
            right_frame = frame.copy()
            
            # Run detections in parallel for fair timing comparison
            with ThreadPoolExecutor(max_workers=2) as executor:
                # HOG detection
                hog_start = time.time()
                hog_future = executor.submit(hog_detect, frame)
                
                # YOLO detection
                yolo_start = time.time()
                yolo_future = executor.submit(yolo_detect, frame)
                
                # Get results
                hog_detections = hog_future.result()
                hog_time = (time.time() - hog_start) * 1000
                
                yolo_detections = yolo_future.result()
                yolo_time = (time.time() - yolo_start) * 1000
            
            hog_stats['time'].append(hog_time)
            yolo_stats['time'].append(yolo_time)
            
            # Draw HOG detections (left side)
            if hog_detections:
                hog_stats['detections'] += 1
                for x, y, w, h, conf in hog_detections:
                    cv2.rectangle(left_frame, (x, y), (x + w, y + h), (0, 0, 255), 2)
                    cv2.putText(left_frame, f'HOG {conf:.2f}', (x, y - 10),
                               cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
            
            # Draw YOLO detections (right side)
            if yolo_detections:
                yolo_stats['detections'] += 1
                for x, y, w, h, conf in yolo_detections:
                    cv2.rectangle(right_frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
                    cv2.putText(right_frame, f'YOLO {conf:.2f}', (x, y - 10),
                               cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
            
            # Calculate statistics
            if hog_stats['time']:
                hog_rate = (hog_stats['detections'] / frame_count) * 100
                hog_avg_time = sum(hog_stats['time']) / len(hog_stats['time'])
            else:
                hog_rate = 0.0
                hog_avg_time = 0.0
                
            if yolo_stats['time']:
                yolo_rate = (yolo_stats['detections'] / frame_count) * 100
                yolo_avg_time = sum(yolo_stats['time']) / len(yolo_stats['time'])
            else:
                yolo_rate = 0.0
                yolo_avg_time = 0.0
            
            # Add labels and statistics
            cv2.putText(left_frame, "HOG DETECTOR", (10, 30),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
            cv2.putText(left_frame, f"Rate: {hog_rate:.1f}%", (10, 60),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)
            cv2.putText(left_frame, f"Time: {hog_avg_time:.1f}ms", (10, 90),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)
            cv2.putText(left_frame, f"Detections: {len(hog_detections)}", (10, 120),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)
            
            cv2.putText(right_frame, "YOLOv8n DETECTOR", (10, 30),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            cv2.putText(right_frame, f"Rate: {yolo_rate:.1f}%", (10, 60),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)
            cv2.putText(right_frame, f"Time: {yolo_avg_time:.1f}ms", (10, 90),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)
            cv2.putText(right_frame, f"Detections: {len(yolo_detections)}", (10, 120),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)
            
            # Combine frames
            combined = np.hstack([left_frame, right_frame])
            
            # Add separator and overall stats
            cv2.line(combined, (width, 0), (width, height), (255, 255, 255), 3)
            
            # Overall comparison at bottom
            improvement = yolo_rate - hog_rate
            cv2.putText(combined, f"Frame {frame_count} | Accuracy Improvement: {improvement:+.1f}%",
                       (10, height - 20), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)
            
            cv2.imshow('Detection Comparison: HOG vs YOLOv8n', combined)
            
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                break
            elif key == ord('s'):
                filename = f'comparison_{int(time.time())}.jpg'
                cv2.imwrite(filename, combined)
                print(f"Saved comparison: {filename}")
    
    except KeyboardInterrupt:
        pass
    finally:
        cap.release()
        cv2.destroyAllWindows()
        
        # Final comparison
        print(f"\nFinal Comparison Results ({frame_count} frames):")
        print("-" * 40)
        print(f"HOG Detector:")
        print(f"  Detection Rate: {hog_rate:.1f}%")
        print(f"  Average Time: {hog_avg_time:.1f}ms")
        print(f"  Total Detections: {hog_stats['detections']}")
        
        print(f"\nYOLOv8n Detector:")
        print(f"  Detection Rate: {yolo_rate:.1f}%") 
        print(f"  Average Time: {yolo_avg_time:.1f}ms")
        print(f"  Total Detections: {yolo_stats['detections']}")
        
        print(f"\nImprovement:")
        print(f"  Accuracy: {improvement:+.1f}%")
        if hog_avg_time > 0 and yolo_avg_time > 0:
            speed_diff = hog_avg_time - yolo_avg_time
            print(f"  Speed: {speed_diff:+.1f}ms (negative = faster)")
        else:
            print("  Speed: Unable to calculate")
        
        if improvement > 10:
            print("\n✓ Significant accuracy improvement with YOLOv8n!")
        elif improvement > 0:
            print("\n✓ YOLOv8n shows better accuracy")
        else:
            print("\n⚠ Results may vary based on lighting and scene")

if __name__ == "__main__":
    run_detection_comparison()