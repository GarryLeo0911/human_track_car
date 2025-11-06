"""
Automatic Human Tracking Car
Main entry point for the human tracking car application with pure visual tracking.
"""

from src.web.app import create_app
from src.control.freenove_motor_controller import FreenoveMotorController
from src.camera.camera_manager import CameraManager
import threading
import logging
import argparse

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

def main():
    """Main function to start the human tracking car system."""
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Human Tracking Car with Enhanced Detection Options')
    parser.add_argument('--detector', 
                       choices=['yolo', 'hog', 'motion', 'edge', 'color', 'enhanced_motion', 'enhanced_edge', 'hybrid', 'auto'], 
                       default='auto',
                       help='Detection method: yolo (YOLOv8n), hog (traditional), motion (basic), edge (basic), color (skin-based), enhanced_motion (improved motion), enhanced_edge (improved edge), hybrid (motion+edge), auto (intelligent selection)')
    parser.add_argument('--platform', 
                       choices=['raspberry_pi_zero', 'raspberry_pi_3', 'raspberry_pi_4', 'other'],
                       default='other',
                       help='Hardware platform for optimal detector selection')
    args = parser.parse_args()
    
    detector_choice = args.detector
    platform = args.platform
    
    logger.info("Starting Human Tracking Car System...")
    logger.info(f"Detection method: {detector_choice}")
    logger.info(f"Hardware platform: {platform}")
    logger.info("Mode: Pure Visual Tracking (no ultrasonic sensor)")
    
    try:
        # Initialize motor controller first (fast)
        logger.info("Initializing Freenove motor controller...")
        motor_controller = FreenoveMotorController()
        logger.info("Freenove motor controller ready")
        
        # Create placeholders for camera and tracker
        camera_manager = None
        human_tracker = None
        
        # Create Flask app with None components initially
        app = create_app(None)
        
        def init_camera_and_tracker():
            """Initialize camera and tracker in background."""
            nonlocal camera_manager, human_tracker
            try:
                logger.info("Initializing camera manager in background...")
                camera_manager = CameraManager()
                logger.info("Camera manager ready")
                
                logger.info("Initializing human tracker...")
                
                # Determine which tracker to use
                if detector_choice in ['motion', 'edge', 'color', 'enhanced_motion', 'enhanced_edge', 'hybrid']:
                    # Use ultra-lightweight trackers (including enhanced versions)
                    from src.tracking.ultra_light_tracker import UltraLightHumanTracker
                    human_tracker = UltraLightHumanTracker(camera_manager, motor_controller, detector_choice)
                    logger.info(f"Ultra-lightweight {detector_choice} tracker ready")
                    
                elif detector_choice == 'yolo':
                    # Force YOLO
                    try:
                        from src.tracking.yolo_human_tracker import YOLOHumanTracker
                        human_tracker = YOLOHumanTracker(camera_manager, motor_controller)
                        logger.info("YOLOv8n human tracker ready (pure visual)")
                    except Exception as e:
                        logger.error(f"Failed to initialize YOLO tracker: {e}")
                        raise
                        
                elif detector_choice == 'hog':
                    # Force HOG
                    from src.tracking.human_tracker import HumanTracker
                    human_tracker = HumanTracker(camera_manager, motor_controller)
                    logger.info("HOG human tracker ready (pure visual)")
                        
                else:  # auto
                    # Intelligent selection based on platform (prefer enhanced detectors)
                    try:
                        from config.lightweight_detector_config import recommend_detector
                        recommended, details = recommend_detector(
                            platform=platform,
                            scenario='real_time_following',
                            performance_target='balanced'
                        )
                        logger.info(f"Auto-selection recommended: {recommended} (based on {details})")
                        
                        # Try recommended lightweight detector first (including enhanced versions)
                        if recommended in ['motion', 'edge', 'color', 'enhanced_motion', 'enhanced_edge', 'hybrid']:
                            from src.tracking.ultra_light_tracker import UltraLightHumanTracker
                            human_tracker = UltraLightHumanTracker(camera_manager, motor_controller, recommended)
                            logger.info(f"Auto-selected ultra-lightweight {recommended} tracker")
                        else:
                            # Fall back to traditional detectors
                            try:
                                from src.tracking.yolo_human_tracker import YOLOHumanTracker
                                human_tracker = YOLOHumanTracker(camera_manager, motor_controller)
                                logger.info("Auto-selected YOLOv8n human tracker")
                            except Exception as e:
                                logger.warning(f"YOLO not available ({e}), falling back to HOG")
                                from src.tracking.human_tracker import HumanTracker
                                human_tracker = HumanTracker(camera_manager, motor_controller)
                                logger.info("Auto-selected HOG human tracker")
                                
                    except Exception as e:
                        logger.warning(f"Auto-selection failed ({e}), using motion detection")
                        from src.tracking.ultra_light_tracker import UltraLightHumanTracker
                        human_tracker = UltraLightHumanTracker(camera_manager, motor_controller, 'motion')
                        logger.info("Fallback: motion detection tracker")
                
                # Update app with real components
                setattr(app, 'human_tracker', human_tracker)  # Safe attribute assignment
                from src.camera.camera_manager import StreamingHandler
                setattr(app, 'streaming_handler', StreamingHandler(camera_manager))  # Safe assignment
                logger.info("All components initialized and connected to Flask app")
                
            except Exception as e:
                logger.error(f"Error initializing camera/tracker: {e}")
                import traceback
                traceback.print_exc()
        
        # Start background initialization
        init_thread = threading.Thread(target=init_camera_and_tracker, daemon=True)
        init_thread.start()
        
        # Start web server immediately
        logger.info("Starting web server on http://0.0.0.0:5000")
        logger.info("Camera and tracking will initialize in background...")
        logger.info("Access the interface at:")
        logger.info("  - http://127.0.0.1:5000")
        logger.info("  - http://localhost:5000")
        logger.info("Motor controller: Freenove 4WD Smart Car Kit compatible")
        
        app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)
        
    except KeyboardInterrupt:
        logger.info("Shutting down...")
    except Exception as e:
        logger.error(f"Error starting application: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Cleanup
        if human_tracker:
            human_tracker.stop_tracking()
        if motor_controller:
            motor_controller.cleanup()
        if camera_manager:
            camera_manager.cleanup()

if __name__ == "__main__":
    main()