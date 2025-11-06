"""
Automatic Human Tracking Car
Main entry point for the human tracking car application with ultrasonic support.
"""

from src.web.app import create_app
from src.tracking.human_tracker import HumanTracker
from src.tracking.ultrasonic_human_tracker import UltrasonicHumanTracker
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
    parser = argparse.ArgumentParser(description='Human Tracking Car with Ultrasonic Support')
    parser.add_argument('--no-ultrasonic', action='store_true', 
                       help='Disable ultrasonic sensor (vision-only mode)')
    parser.add_argument('--ultrasonic-pins', nargs=2, type=int, default=[27, 22],
                       help='Ultrasonic sensor GPIO pins [trigger echo] (default: 27 22)')
    args = parser.parse_args()
    
    use_ultrasonic = not args.no_ultrasonic
    
    logger.info("Starting Human Tracking Car System...")
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
                if use_ultrasonic:
                    # Use enhanced tracker with ultrasonic support
                    human_tracker = UltrasonicHumanTracker(camera_manager, motor_controller, use_ultrasonic=True)
                    logger.info("Enhanced human tracker with ultrasonic support ready")
                else:
                    # Use standard vision-only tracker
                    human_tracker = HumanTracker(camera_manager, motor_controller)
                    logger.info("Standard human tracker ready")
                
                # Update app with real components
                setattr(app, 'human_tracker', human_tracker)  # Safe attribute assignment
                from src.camera.camera_manager import StreamingHandler
                setattr(app, 'streaming_handler', StreamingHandler(camera_manager))  # Safe assignment
                logger.info("All components initialized and connected to Flask app")
                
            except Exception as e:
                logger.error(f"Error initializing camera/tracker: {e}")
        
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