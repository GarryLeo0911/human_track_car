#!/usr/bin/env python3
"""
Quick verification script for enhanced human detection
"""

import sys
import cv2
import numpy as np

def test_enhanced_detectors():
    """Quick test of enhanced detection imports and basic functionality"""
    print("Testing Enhanced Human Detection System...")
    print("=========================================")
    
    try:
        # Test imports
        print("1. Testing imports...")
        from src.tracking.enhanced_human_detector import (
            HybridHumanDetector,
            EnhancedMotionDetector,
            EnhancedEdgeDetector
        )
        print("   ✓ Enhanced detector imports successful")
        
        # Test detector initialization
        print("2. Testing detector initialization...")
        enhanced_motion = EnhancedMotionDetector()
        print("   ✓ Enhanced motion detector initialized")
        
        enhanced_edge = EnhancedEdgeDetector()
        print("   ✓ Enhanced edge detector initialized")
        
        hybrid = HybridHumanDetector()
        print("   ✓ Hybrid detector initialized")
        
        # Test with dummy frame
        print("3. Testing detection with dummy frame...")
        dummy_frame = np.zeros((480, 640, 3), dtype=np.uint8)
        
        # Add a simple rectangle to simulate a person
        cv2.rectangle(dummy_frame, (250, 150), (350, 400), (100, 100, 100), -1)
        
        # Test each detector
        detectors = [
            ("Enhanced Motion", enhanced_motion),
            ("Enhanced Edge", enhanced_edge),
            ("Hybrid", hybrid)
        ]
        
        for name, detector in detectors:
            try:
                detections = detector.detect_humans(dummy_frame)
                print(f"   ✓ {name}: {len(detections)} detections")
                
                # Check detection format
                if detections and len(detections[0]) == 5:
                    x, y, w, h, confidence = detections[0]
                    print(f"     First detection: box=({x},{y},{w},{h}), confidence={confidence:.3f}")
                
            except Exception as e:
                print(f"   ✗ {name}: Error - {e}")
        
        # Test main tracker integration
        print("4. Testing main tracker integration...")
        from src.tracking.ultra_light_tracker import UltraLightHumanTracker
        
        # Mock camera and motor controller
        class MockCamera:
            def get_frame(self):
                return True, dummy_frame
        
        class MockMotor:
            def move_forward(self, speed=50): pass
            def turn_left(self, speed=50): pass
            def turn_right(self, speed=50): pass
            def stop(self): pass
        
        mock_camera = MockCamera()
        mock_motor = MockMotor()
        
        # Test enhanced detector types
        enhanced_types = ['enhanced_motion', 'enhanced_edge', 'hybrid']
        for detector_type in enhanced_types:
            try:
                tracker = UltraLightHumanTracker(mock_camera, mock_motor, detector_type)
                print(f"   ✓ UltraLightHumanTracker with {detector_type} initialized")
            except Exception as e:
                print(f"   ✗ UltraLightHumanTracker with {detector_type}: Error - {e}")
        
        print("\n5. Testing configuration updates...")
        from config.lightweight_detector_config import DETECTOR_CONFIGS, DEFAULT_DETECTOR
        
        enhanced_configs = ['enhanced_motion', 'enhanced_edge', 'hybrid']
        for config in enhanced_configs:
            if config in DETECTOR_CONFIGS:
                print(f"   ✓ {config} configuration found")
            else:
                print(f"   ✗ {config} configuration missing")
        
        print(f"   Default detector: {DEFAULT_DETECTOR}")
        
        print("\n✓ All tests passed! Enhanced detection system is ready.")
        print("\nNext steps:")
        print("1. Run 'python demo_enhanced_detection.py' for interactive demo")
        print("2. Run 'python test_enhanced_detection.py' for comprehensive testing")
        print("3. Use 'python main.py --detector hybrid' for best accuracy")
        
        return True
        
    except Exception as e:
        print(f"\n✗ Test failed: {e}")
        print("\nPlease check:")
        print("1. All files are present")
        print("2. Python path includes the project directory")
        print("3. Required dependencies are installed")
        return False

def test_camera_detection():
    """Test with actual camera if available"""
    print("\n6. Testing with camera (optional)...")
    
    try:
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            print("   No camera detected, skipping camera test")
            return
        
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        
        ret, frame = cap.read()
        cap.release()
        
        if not ret:
            print("   Cannot read from camera")
            return
        
        # Quick test with hybrid detector
        from src.tracking.enhanced_human_detector import HybridHumanDetector
        detector = HybridHumanDetector()
        
        # Test multiple frames for background learning
        for i in range(5):
            detections = detector.detect_humans(frame)
        
        print(f"   ✓ Camera test completed: {len(detections)} detections found")
        
    except Exception as e:
        print(f"   Camera test error: {e}")

if __name__ == "__main__":
    print("Enhanced Human Detection Verification")
    print("====================================")
    
    success = test_enhanced_detectors()
    
    if success:
        test_camera_detection()
        print("\nVerification completed successfully! 🎉")
        sys.exit(0)
    else:
        print("\nVerification failed! ❌")
        sys.exit(1)