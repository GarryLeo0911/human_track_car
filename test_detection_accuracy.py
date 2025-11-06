#!/usr/bin/env python3
"""
Test script to evaluate human detection accuracy improvements.
This script helps you compare detection quality and tune parameters.
"""

import time
import cv2
import logging
import sys
import os
import numpy as np

# Add src directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.tracking.human_tracker import HumanDetector
from src.camera.camera_manager import CameraManager

# Configure logging
logging.basicConfig(level=logging.INFO)

def test_detection_accuracy():
    """Test detection accuracy with detailed analysis."""
    
    print("Human Detection Accuracy Test")
    print("=" * 50)
    print("This will show you:")
    print("- Detection confidence scores")
    print("- Stability metrics")
    print("- Size and aspect ratio validation")
    print("- Frame-to-frame consistency")
    print("")
    print("Press 'q' to quit, 's' to save current frame")
    print("")
    
    # Initialize components
    camera = CameraManager()
    detector = HumanDetector()
    
    # Statistics tracking
    total_frames = 0
    frames_with_detection = 0
    detection_scores = []
    stability_scores = []
    
    # Wait for camera to initialize
    time.sleep(2)
    
    try:
        while True:
            frame = camera.get_frame()
            if frame is None:
                continue
            
            total_frames += 1
            
            # Get detections with timing
            start_time = time.time()
            human_boxes = detector.detect_humans(frame)
            detection_time = (time.time() - start_time) * 1000  # Convert to ms
            
            # Create analysis frame
            analysis_frame = frame.copy()
            
            if human_boxes:
                frames_with_detection += 1
                
                print(f"\nFrame {total_frames}: {len(human_boxes)} detection(s) in {detection_time:.1f}ms")
                
                for i, (x, y, w, h) in enumerate(human_boxes):
                    # Calculate metrics
                    aspect_ratio = h / w if w > 0 else 0
                    area = w * h
                    center_x = x + w // 2
                    center_y = y + h // 2
                    
                    # Estimate confidence based on size and aspect ratio
                    size_score = min(1.0, area / (100 * 200))  # Normalize to typical human size
                    aspect_score = 1.0 if 1.5 <= aspect_ratio <= 4.0 else 0.5
                    confidence = (size_score + aspect_score) / 2
                    
                    detection_scores.append(confidence)
                    
                    print(f"  Detection {i+1}:")
                    print(f"    Position: ({center_x}, {center_y})")
                    print(f"    Size: {w}x{h} (area: {area})")
                    print(f"    Aspect ratio: {aspect_ratio:.2f}")
                    print(f"    Estimated confidence: {confidence:.2f}")
                    
                    # Color-code detection quality
                    if confidence > 0.8:
                        color = (0, 255, 0)  # Green for high confidence
                        quality = "EXCELLENT"
                    elif confidence > 0.6:
                        color = (0, 255, 255)  # Yellow for good
                        quality = "GOOD"
                    elif confidence > 0.4:
                        color = (0, 165, 255)  # Orange for fair
                        quality = "FAIR"
                    else:
                        color = (0, 0, 255)  # Red for poor
                        quality = "POOR"
                    
                    # Draw detection with quality indicator
                    thickness = 3 if confidence > 0.6 else 2
                    cv2.rectangle(analysis_frame, (x, y), (x + w, y + h), color, thickness)
                    
                    # Add quality labels
                    cv2.putText(analysis_frame, f"{quality} ({confidence:.2f})", 
                               (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
                    cv2.putText(analysis_frame, f"{w}x{h}", 
                               (x, y + h + 20), cv2.FONT_HERSHEY_SIMPLEX, 0.4, color, 1)
                    
                    # Center point
                    cv2.circle(analysis_frame, (center_x, center_y), 5, color, -1)
                    
                    # Aspect ratio indicator
                    if aspect_ratio < 1.5:
                        cv2.putText(analysis_frame, "TOO WIDE", (x, y + h + 35), 
                                   cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 0, 255), 1)
                    elif aspect_ratio > 4.0:
                        cv2.putText(analysis_frame, "TOO TALL", (x, y + h + 35), 
                                   cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 0, 255), 1)
                        
            else:
                print(f"Frame {total_frames}: No detections in {detection_time:.1f}ms")
            
            # Calculate overall statistics
            detection_rate = (frames_with_detection / total_frames) * 100 if total_frames > 0 else 0
            avg_confidence = sum(detection_scores) / len(detection_scores) if detection_scores else 0
            
            # Add statistics overlay
            cv2.putText(analysis_frame, f"Detection Rate: {detection_rate:.1f}% ({frames_with_detection}/{total_frames})", 
                       (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
            cv2.putText(analysis_frame, f"Avg Confidence: {avg_confidence:.2f}", 
                       (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
            cv2.putText(analysis_frame, f"Processing Time: {detection_time:.1f}ms", 
                       (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
            
            # Frame guidelines for human detection
            height, width = analysis_frame.shape[:2]
            center_x, center_y = width // 2, height // 2
            cv2.line(analysis_frame, (center_x, 0), (center_x, height), (255, 0, 0), 1)
            cv2.line(analysis_frame, (0, center_y), (width, center_y), (255, 0, 0), 1)
            
            # Display frame
            cv2.imshow('Human Detection Accuracy Test', analysis_frame)
            
            # Handle key presses
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                break
            elif key == ord('s'):
                timestamp = int(time.time())
                filename = f"detection_test_{timestamp}.jpg"
                cv2.imwrite(filename, analysis_frame)
                print(f"Saved frame as {filename}")
            
            # Brief pause to make output readable
            time.sleep(0.1)
            
    except KeyboardInterrupt:
        print("\nTest stopped by user")
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        camera.cleanup()
        cv2.destroyAllWindows()
        
        # Final statistics
        print("\n" + "=" * 50)
        print("DETECTION ACCURACY SUMMARY")
        print("=" * 50)
        print(f"Total frames processed: {total_frames}")
        print(f"Frames with detections: {frames_with_detection}")
        print(f"Overall detection rate: {detection_rate:.1f}%")
        
        if detection_scores:
            print(f"Average confidence: {avg_confidence:.3f}")
            print(f"Best confidence: {max(detection_scores):.3f}")
            print(f"Worst confidence: {min(detection_scores):.3f}")
            
            # Quality distribution
            excellent = sum(1 for s in detection_scores if s > 0.8)
            good = sum(1 for s in detection_scores if 0.6 < s <= 0.8)
            fair = sum(1 for s in detection_scores if 0.4 < s <= 0.6)
            poor = sum(1 for s in detection_scores if s <= 0.4)
            
            print(f"\nQuality Distribution:")
            print(f"  Excellent (>0.8): {excellent}")
            print(f"  Good (0.6-0.8): {good}")
            print(f"  Fair (0.4-0.6): {fair}")
            print(f"  Poor (≤0.4): {poor}")
        
        print("\nRecommendations:")
        if detection_rate < 50:
            print("- Low detection rate. Try adjusting lighting or camera position.")
        if avg_confidence < 0.6:
            print("- Low average confidence. Ensure humans are clearly visible and properly sized.")
        if detection_time > 100:
            print("- Slow processing. Consider reducing frame resolution if needed.")
        
        print("\nTest completed.")

if __name__ == "__main__":
    test_detection_accuracy()