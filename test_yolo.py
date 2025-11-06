#!/usr/bin/env python3
"""
Test YOLOv8n Human Detection
Quick test script to verify YOLO installation and detection capability.
"""

import cv2
import time
import sys
import os

# Add src directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

def test_yolo_detection():
    """Test YOLOv8n human detection."""
    
    print("YOLOv8n Human Detection Test")
    print("=" * 40)
    
    try:
        # Test YOLO import
        print("Testing ultralytics import...")
        try:
            from ultralytics import YOLO
            print("✓ ultralytics imported successfully")
        except ImportError as e:
            print(f"✗ Failed to import ultralytics: {e}")
            print("\nTo install YOLOv8, run:")
            print("pip install ultralytics torch torchvision")
            return False
        
        # Test YOLOv8n model loading
        print("\nLoading YOLOv8n model...")
        try:
            model = YOLO('yolov8n.pt')
            print("✓ YOLOv8n model loaded successfully")
            print(f"  Model path: {model.model}")
        except Exception as e:
            print(f"✗ Failed to load YOLOv8n: {e}")
            return False
        
        # Test camera
        print("\nTesting camera...")
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            print("✗ Could not open camera")
            print("Make sure a camera is connected")
            return False
        
        print("✓ Camera opened successfully")
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        
        print("\nStarting detection test...")
        print("Press 'q' to quit, 's' to save a detection image")
        print("Look for green boxes around detected people")
        
        frame_count = 0
        detection_count = 0
        total_time = 0
        
        while True:
            ret, frame = cap.read()
            if not ret:
                continue
            
            frame_count += 1
            
            # Run YOLO detection
            start_time = time.time()
            results = model(frame, conf=0.5, classes=[0], verbose=False)  # Class 0 = person
            detection_time = time.time() - start_time
            total_time += detection_time
            
            # Process results
            persons_detected = 0
            if results and len(results) > 0:
                result = results[0]
                if result.boxes is not None:
                    boxes = result.boxes.xyxy.cpu().numpy()
                    confidences = result.boxes.conf.cpu().numpy()
                    
                    for box, conf in zip(boxes, confidences):
                        x1, y1, x2, y2 = box.astype(int)
                        w, h = x2 - x1, y2 - y1
                        
                        # Draw detection
                        color = (0, 255, 0)  # Green
                        cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
                        cv2.putText(frame, f'Person {conf:.2f}', 
                                   (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
                        
                        persons_detected += 1
            
            if persons_detected > 0:
                detection_count += 1
            
            # Add statistics
            avg_time = total_time / frame_count if frame_count > 0 else 0
            detection_rate = detection_count / frame_count * 100 if frame_count > 0 else 0
            
            cv2.putText(frame, f'YOLOv8n Detection Test', 
                       (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            cv2.putText(frame, f'Persons: {persons_detected} | Time: {detection_time*1000:.1f}ms', 
                       (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)
            cv2.putText(frame, f'Detection Rate: {detection_rate:.1f}% | Avg: {avg_time*1000:.1f}ms', 
                       (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)
            cv2.putText(frame, f'Frame {frame_count}', 
                       (10, frame.shape[0] - 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)
            
            cv2.imshow('YOLOv8n Test', frame)
            
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                break
            elif key == ord('s') and persons_detected > 0:
                filename = f'yolo_detection_{int(time.time())}.jpg'
                cv2.imwrite(filename, frame)
                print(f"Saved detection image: {filename}")
        
        cap.release()
        cv2.destroyAllWindows()
        
        # Final statistics
        print(f"\nTest Results:")
        print(f"Total frames: {frame_count}")
        print(f"Frames with detections: {detection_count}")
        print(f"Detection rate: {detection_rate:.1f}%")
        print(f"Average detection time: {avg_time*1000:.1f}ms")
        
        if detection_rate > 50:
            print("✓ YOLO detection working well!")
        elif detection_rate > 20:
            print("⚠ YOLO detection working but low rate (lighting/positioning?)")
        else:
            print("⚠ Low detection rate - check camera positioning and lighting")
            
        return True
        
    except KeyboardInterrupt:
        print("\nTest interrupted by user")
        return True
    except Exception as e:
        print(f"\nTest failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def check_requirements():
    """Check if all requirements are installed."""
    print("Checking Requirements:")
    print("-" * 20)
    
    # Check ultralytics
    try:
        import ultralytics
        print(f"✓ ultralytics: {ultralytics.__version__}")
    except ImportError:
        print("✗ ultralytics not installed")
        return False
    
    # Check torch
    try:
        import torch
        print(f"✓ torch: {torch.__version__}")
    except ImportError:
        print("✗ torch not installed")
        return False
    
    # Check OpenCV
    try:
        import cv2
        print(f"✓ opencv-python: {cv2.__version__}")
    except ImportError:
        print("✗ opencv-python not installed")
        return False
    
    print("✓ All requirements satisfied")
    return True

if __name__ == "__main__":
    print("YOLOv8n Human Detection Test Tool")
    print("=" * 50)
    
    if not check_requirements():
        print("\nMissing requirements. Install with:")
        print("pip install ultralytics torch torchvision opencv-python")
        sys.exit(1)
    
    print("\nStarting detection test...")
    success = test_yolo_detection()
    
    if success:
        print("\n✓ YOLOv8n test completed successfully!")
        print("\nYou can now use YOLO detection in the main application:")
        print("python main.py --detector yolo")
    else:
        print("\n✗ YOLOv8n test failed")
        print("Check error messages above and try:")
        print("python main.py --detector hog  # Use traditional detection")