"""
Automatic Human Tracking Car
Main entry point for the human tracking car application with YOLO and ultrasonic support.
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
    parser = argparse.ArgumentParser(description='Human Tracking Car with YOLO and Ultrasonic Support')
    parser.add_argument('--no-ultrasonic', action='store_true', 
                       help='Disable ultrasonic sensor (vision-only mode)')
    parser.add_argument('--ultrasonic-pins', nargs=2, type=int, default=[27, 22],
                       help='Ultrasonic sensor GPIO pins [trigger echo] (default: 27 22)')
    parser.add_argument('--detector', choices=['yolo', 'hog', 'auto'], default='auto',
                       help='Detection method: yolo (YOLOv8n), hog (traditional), auto (try YOLO first)')
    args = parser.parse_args()
    
    use_ultrasonic = not args.no_ultrasonic
    detector_choice = args.detector
    
    logger.info("Starting Human Tracking Car System...")
    logger.info(f"Detection method: {detector_choice}")
    if use_ultrasonic:
        logger.info("Enhanced mode: Vision + Ultrasonic sensor")
    else:
        logger.info("Standard mode: Vision only")
    
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
                if detector_choice == 'yolo':
                    # Force YOLO
                    try:
                        from src.tracking.yolo_human_tracker import YOLOHumanTracker
                        if use_ultrasonic:
                            # TODO: Create YOLO + Ultrasonic tracker
                            logger.warning("YOLO + Ultrasonic not yet implemented, using YOLO only")
                            human_tracker = YOLOHumanTracker(camera_manager, motor_controller)
                        else:
                            human_tracker = YOLOHumanTracker(camera_manager, motor_controller)
                        logger.info("YOLOv8n human tracker ready")
                    except Exception as e:
                        logger.error(f"Failed to initialize YOLO tracker: {e}")
                        raise
                        
                elif detector_choice == 'hog':
                    # Force HOG
                    from src.tracking.human_tracker import HumanTracker
                    from src.tracking.ultrasonic_human_tracker import UltrasonicHumanTracker
                    if use_ultrasonic:
                        human_tracker = UltrasonicHumanTracker(camera_manager, motor_controller, use_ultrasonic=True)
                        logger.info("HOG + Ultrasonic human tracker ready")
                    else:
                        human_tracker = HumanTracker(camera_manager, motor_controller)
                        logger.info("HOG human tracker ready")
                        
                else:  # auto
                    # Try YOLO first, fallback to HOG
                    try:
                        from src.tracking.yolo_human_tracker import YOLOHumanTracker
                        if use_ultrasonic:
                            logger.warning("YOLO + Ultrasonic not yet implemented, using YOLO only")
                            human_tracker = YOLOHumanTracker(camera_manager, motor_controller)
                        else:
                            human_tracker = YOLOHumanTracker(camera_manager, motor_controller)
                        logger.info("Auto-selected YOLOv8n human tracker")
                    except Exception as e:
                        logger.warning(f"YOLO not available ({e}), falling back to HOG")
                        from src.tracking.human_tracker import HumanTracker
                        from src.tracking.ultrasonic_human_tracker import UltrasonicHumanTracker
                        if use_ultrasonic:
                            human_tracker = UltrasonicHumanTracker(camera_manager, motor_controller, use_ultrasonic=True)
                            logger.info("Fallback: HOG + Ultrasonic human tracker ready")
                        else:
                            human_tracker = HumanTracker(camera_manager, motor_controller)
                            logger.info("Fallback: HOG human tracker ready")
                
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