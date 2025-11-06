"""
Lightweight Detector Performance Test
Compare the performance of different lightweight human detection solutions
"""

import cv2
import time
import numpy as np
import sys
import os

# 添加项目路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.tracking.ultra_light_tracker import (
    MotionBasedDetector,
    EdgeBasedDetector,
    ColorBasedDetector
)

def test_detector_performance():
    """Test the performance of different detectors"""
    
    # Initialize detectors
    detectors = {
        'motion': MotionBasedDetector(),
        'edge': EdgeBasedDetector(),
        'color': ColorBasedDetector()
    }
    
    # Performance statistics
    performance_stats = {
        'motion': {'times': [], 'detections': 0},
        'edge': {'times': [], 'detections': 0},
        'color': {'times': [], 'detections': 0}
    }
    
    # Open camera
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Cannot open camera")
        return
    
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    cap.set(cv2.CAP_PROP_FPS, 30)
    
    frame_count = 0
    max_frames = 100  # Test 100 frames
    
    print("Starting performance test...")
    print("Please move in front of the camera to test detection performance")
    print("Press 'q' to exit test")
    
    while frame_count < max_frames:
        ret, frame = cap.read()
        if not ret:
            continue
        
        frame_count += 1
        
        # 创建显示画布
        display_frame = frame.copy()
        height, width = frame.shape[:2]
        
        # 为每个检测器分配显示区域
        detector_height = height // 3
        y_offset = 0
        
        for detector_name, detector in detectors.items():
            # 测试检测时间
            start_time = time.time()
            detections = detector.detect_humans(frame)
            detection_time = (time.time() - start_time) * 1000
            
            # 记录统计信息
            performance_stats[detector_name]['times'].append(detection_time)
            if detections:
                performance_stats[detector_name]['detections'] += 1
            
            # 在对应区域绘制检测结果
            detector_region = display_frame[y_offset:y_offset + detector_height, :]
            
            # 绘制检测框
            for x, y, w, h in detections:
                # 调整坐标到当前区域
                adj_y = int(y * detector_height / height) + y_offset
                adj_h = int(h * detector_height / height)
                adj_x = x
                adj_w = w
                
                cv2.rectangle(display_frame, (adj_x, adj_y), 
                            (adj_x + adj_w, adj_y + adj_h), (0, 255, 0), 2)
            
            # 显示性能信息
            info_text = f"{detector_name}: {detection_time:.1f}ms, {len(detections)} detections"
            cv2.putText(display_frame, info_text, 
                       (10, y_offset + 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
            
            # 绘制分隔线
            if y_offset + detector_height < height:
                cv2.line(display_frame, (0, y_offset + detector_height), 
                        (width, y_offset + detector_height), (255, 255, 255), 2)
            
            y_offset += detector_height
        
        # Display overall progress
        progress = f"Frame: {frame_count}/{max_frames}"
        cv2.putText(display_frame, progress, 
                   (width - 200, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
        
        # Show frame
        cv2.imshow('Lightweight Detector Performance Test', display_frame)
        
        # Check exit condition
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break
    
    # Cleanup
    cap.release()
    cv2.destroyAllWindows()
    
    # Calculate and display statistics
    print("\n=== Performance Test Results ===")
    print(f"Total test frames: {frame_count}")
    print()
    
    for detector_name, stats in performance_stats.items():
        if stats['times']:
            avg_time = np.mean(stats['times'])
            min_time = np.min(stats['times'])
            max_time = np.max(stats['times'])
            detection_rate = (stats['detections'] / frame_count) * 100
            
            print(f"{detector_name.upper()} Detector:")
            print(f"  Average detection time: {avg_time:.2f}ms")
            print(f"  Fastest detection time: {min_time:.2f}ms")
            print(f"  Slowest detection time: {max_time:.2f}ms")
            print(f"  Detection success rate: {detection_rate:.1f}%")
            print(f"  Theoretical max FPS: {1000/avg_time:.1f}")
            print()

def compare_with_existing():
    """Compare with existing YOLO and HOG detectors"""
    print("\n=== Comparison with Existing Detectors ===")
    
    # Simulated performance data (based on typical Raspberry Pi 4 performance)
    comparison_data = {
        'YOLOv8n': {
            'avg_time': 150,  # 150ms
            'memory': '~200MB',
            'cpu_usage': '~80%',
            'accuracy': '90%'
        },
        'HOG': {
            'avg_time': 80,   # 80ms
            'memory': '~50MB',
            'cpu_usage': '~40%',
            'accuracy': '70%'
        },
        'Motion': {
            'avg_time': 15,   # 15ms
            'memory': '~10MB',
            'cpu_usage': '~15%',
            'accuracy': '60%'
        },
        'Edge': {
            'avg_time': 25,   # 25ms
            'memory': '~15MB',
            'cpu_usage': '~20%',
            'accuracy': '50%'
        },
        'Color': {
            'avg_time': 20,   # 20ms
            'memory': '~12MB',
            'cpu_usage': '~18%',
            'accuracy': '45%'
        }
    }
    
    print(f"{'Detector':<10} {'Det.Time':<10} {'Memory':<10} {'CPU Usage':<10} {'Accuracy':<10} {'FPS':<10}")
    print("-" * 70)
    
    for detector, stats in comparison_data.items():
        fps = 1000 / stats['avg_time']
        print(f"{detector:<10} {stats['avg_time']:<10}ms {stats['memory']:<10} {stats['cpu_usage']:<10} {stats['accuracy']:<10} {fps:<10.1f}")
    
    print("\nRecommended Solutions:")
    print("1. For highest performance and accuracy: YOLOv8n (requires powerful hardware)")
    print("2. For balanced performance and accuracy: HOG detector")
    print("3. For ultra-lightweight: Motion detector")
    print("4. For stable lighting environments: Edge detector")
    print("5. For indoor environments: Color detector")

def main():
    """Main function"""
    print("Lightweight Human Detector Performance Testing Tool")
    print("=" * 40)
    
    choice = input("\nSelect test mode:\n1. Real-time performance test\n2. Performance comparison analysis\nEnter choice (1/2): ")
    
    if choice == '1':
        test_detector_performance()
    elif choice == '2':
        compare_with_existing()
    else:
        print("Invalid choice, running performance comparison analysis...")
        compare_with_existing()

if __name__ == "__main__":
    main()