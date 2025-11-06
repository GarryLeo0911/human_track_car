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
        # Initialize components
        camera_manager = CameraManager()
        motor_controller = MotorController()
        human_tracker = HumanTracker(camera_manager, motor_controller)
        
        # Create Flask app
        app = create_app(human_tracker)
        
        # Start tracking in a separate thread
        tracking_thread = threading.Thread(
            target=human_tracker.start_tracking,
            daemon=True
        )
        tracking_thread.start()
        
        # Start web server
        logger.info("Starting web server on http://0.0.0.0:5000")
        app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)
        
    except KeyboardInterrupt:
        logger.info("Shutting down...")
    except Exception as e:
        logger.error(f"Error starting application: {e}")
    finally:
        # Cleanup
        if 'human_tracker' in locals():
            human_tracker.stop_tracking()
        if 'motor_controller' in locals():
            motor_controller.cleanup()
        if 'camera_manager' in locals():
            camera_manager.cleanup()

if __name__ == "__main__":
    main()