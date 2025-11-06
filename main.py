"""
Automatic Human Tracking Car
Main entry point for the human tracking car application.
"""

from src.web.app import create_app
from src.tracking.human_tracker import HumanTracker
from src.control.motor_controller import MotorController
from src.camera.camera_manager import CameraManager
import threading
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

def main():
    """Main function to start the human tracking car system."""
    logger.info("Starting Human Tracking Car System...")
    
    try:
        # Initialize motor controller first (fast)
        logger.info("Initializing motor controller...")
        motor_controller = MotorController()
        logger.info("Motor controller ready")
        
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
                human_tracker = HumanTracker(camera_manager, motor_controller)
                logger.info("Human tracker ready")
                
                # Update app with real components
                app.human_tracker = human_tracker
                from src.camera.camera_manager import StreamingHandler
                app.streaming_handler = StreamingHandler(camera_manager)
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