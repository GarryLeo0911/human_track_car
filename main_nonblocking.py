"""
Non-blocking version of main.py
"""

from src.web.app import create_app
from src.tracking.human_tracker import HumanTracker
from src.control.motor_controller import MotorController
from src.camera.camera_manager import CameraManager
import threading
import logging
import time

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

class NonBlockingApp:
    """Non-blocking application wrapper."""
    
    def __init__(self):
        self.camera_manager = None
        self.motor_controller = None
        self.human_tracker = None
        self.app = None
        self.components_ready = False
        
    def init_components_async(self):
        """Initialize components in background thread."""
        logger.info("Initializing components in background...")
        
        try:
            # Initialize motor controller first (should be fast)
            logger.info("Initializing motor controller...")
            self.motor_controller = MotorController()
            logger.info("Motor controller ready")
            
            # Initialize camera (potentially slow)
            logger.info("Initializing camera manager...")
            self.camera_manager = CameraManager()
            logger.info("Camera manager ready")
            
            # Initialize tracker
            logger.info("Initializing human tracker...")
            self.human_tracker = HumanTracker(self.camera_manager, self.motor_controller)
            logger.info("Human tracker ready")
            
            # Update Flask app with initialized components
            if self.app:
                self.app.human_tracker = self.human_tracker
                from src.camera.camera_manager import StreamingHandler
                self.app.streaming_handler = StreamingHandler(self.camera_manager)
                
            self.components_ready = True
            logger.info("All components initialized successfully!")
            
        except Exception as e:
            logger.error(f"Error initializing components: {e}")
            import traceback
            traceback.print_exc()
            
    def create_placeholder_app(self):
        """Create Flask app with placeholder components."""
        from flask import Flask, render_template, Response, jsonify, request
        import time
        
        app = Flask(__name__, 
                    template_folder='templates',
                    static_folder='static')
        
        @app.route('/')
        def index():
            """Main control interface."""
            return render_template('index.html')
            
        @app.route('/video_feed')
        def video_feed():
            """Video streaming route."""
            def generate():
                while True:
                    try:
                        if self.components_ready and hasattr(app, 'streaming_handler'):
                            # Use real camera stream
                            for frame in app.streaming_handler.generate_mjpeg_stream():
                                yield frame
                                break
                        else:
                            # Generate placeholder frame
                            import cv2
                            import numpy as np
                            
                            frame = np.zeros((480, 640, 3), dtype=np.uint8)
                            status_text = "Initializing camera..." if not self.components_ready else "Camera not available"
                            cv2.putText(frame, status_text, (50, 240), 
                                       cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
                            
                            ret, buffer = cv2.imencode('.jpg', frame)
                            if ret:
                                frame_bytes = buffer.tobytes()
                                yield (b'--frame\r\n'
                                       b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
                            
                        time.sleep(0.1)
                        
                    except Exception as e:
                        logger.error(f"Error in video feed: {e}")
                        time.sleep(1)
                        
            return Response(generate(),
                           mimetype='multipart/x-mixed-replace; boundary=frame')
            
        @app.route('/api/status')
        def get_status():
            """Get system status."""
            try:
                if self.components_ready and self.human_tracker:
                    tracking_status = self.human_tracker.get_tracking_status()
                    motor_status = self.human_tracker.motor_controller.get_status()
                    camera_status = self.human_tracker.camera_manager.get_status()
                else:
                    tracking_status = {'tracking': False, 'last_human_center': None}
                    motor_status = {'is_moving': False, 'rpi_mode': False}
                    camera_status = {'camera_active': False, 'framerate': 0}
                
                return jsonify({
                    'tracking': tracking_status,
                    'motor': motor_status,
                    'camera': camera_status,
                    'components_ready': self.components_ready,
                    'timestamp': time.time()
                })
            except Exception as e:
                logger.error(f"Error getting status: {e}")
                return jsonify({'error': str(e), 'components_ready': False}), 500
                
        @app.route('/api/control/start', methods=['POST'])
        def start_tracking():
            """Start human tracking."""
            try:
                if not self.components_ready:
                    return jsonify({'error': 'Components not ready yet'}), 503
                    
                if not self.human_tracker.tracking:
                    tracking_thread = threading.Thread(
                        target=self.human_tracker.start_tracking,
                        daemon=True
                    )
                    tracking_thread.start()
                    
                return jsonify({'status': 'tracking_started'})
            except Exception as e:
                logger.error(f"Error starting tracking: {e}")
                return jsonify({'error': str(e)}), 500
                
        @app.route('/api/control/stop', methods=['POST'])
        def stop_tracking():
            """Stop human tracking."""
            try:
                if self.components_ready and self.human_tracker:
                    self.human_tracker.stop_tracking()
                return jsonify({'status': 'tracking_stopped'})
            except Exception as e:
                logger.error(f"Error stopping tracking: {e}")
                return jsonify({'error': str(e)}), 500
                
        @app.route('/api/control/manual', methods=['POST'])
        def manual_control():
            """Manual motor control."""
            try:
                if not self.components_ready:
                    return jsonify({'error': 'Components not ready yet'}), 503
                    
                data = request.get_json()
                if not data:
                    return jsonify({'error': 'No data provided'}), 400
                    
                action = data.get('action')
                speed = data.get('speed', 50)
                
                # Stop tracking for manual control
                if self.human_tracker:
                    self.human_tracker.stop_tracking()
                
                # Execute manual command
                motor_controller = self.human_tracker.motor_controller
                
                if action == 'forward':
                    motor_controller.move_forward(speed)
                elif action == 'backward':
                    motor_controller.move_backward(speed)
                elif action == 'left':
                    motor_controller.turn_left(speed)
                elif action == 'right':
                    motor_controller.turn_right(speed)
                elif action == 'stop':
                    motor_controller.stop()
                else:
                    return jsonify({'error': 'Invalid action'}), 400
                    
                return jsonify({'status': f'executed_{action}'})
                
            except Exception as e:
                logger.error(f"Error in manual control: {e}")
                return jsonify({'error': str(e)}), 500
                
        @app.route('/api/settings', methods=['GET', 'POST'])
        def settings():
            """Get or update tracking settings."""
            try:
                if not self.components_ready:
                    # Return default settings
                    if request.method == 'GET':
                        return jsonify({
                            'target_distance': 150,
                            'pid_x': {'kp': 0.5, 'ki': 0.1, 'kd': 0.2},
                            'pid_distance': {'kp': 0.3, 'ki': 0.05, 'kd': 0.1}
                        })
                    else:
                        return jsonify({'error': 'Components not ready yet'}), 503
                        
                if request.method == 'GET':
                    return jsonify({
                        'target_distance': self.human_tracker.target_distance,
                        'pid_x': {
                            'kp': self.human_tracker.pid_x.kp,
                            'ki': self.human_tracker.pid_x.ki,
                            'kd': self.human_tracker.pid_x.kd
                        },
                        'pid_distance': {
                            'kp': self.human_tracker.pid_distance.kp,
                            'ki': self.human_tracker.pid_distance.ki,
                            'kd': self.human_tracker.pid_distance.kd
                        }
                    })
                else:
                    data = request.get_json()
                    
                    if 'target_distance' in data:
                        self.human_tracker.target_distance = data['target_distance']
                        
                    if 'pid_x' in data:
                        pid_data = data['pid_x']
                        self.human_tracker.pid_x.kp = pid_data.get('kp', self.human_tracker.pid_x.kp)
                        self.human_tracker.pid_x.ki = pid_data.get('ki', self.human_tracker.pid_x.ki)
                        self.human_tracker.pid_x.kd = pid_data.get('kd', self.human_tracker.pid_x.kd)
                        
                    if 'pid_distance' in data:
                        pid_data = data['pid_distance']
                        self.human_tracker.pid_distance.kp = pid_data.get('kp', self.human_tracker.pid_distance.kp)
                        self.human_tracker.pid_distance.ki = pid_data.get('ki', self.human_tracker.pid_distance.ki)
                        self.human_tracker.pid_distance.kd = pid_data.get('kd', self.human_tracker.pid_distance.kd)
                        
                    return jsonify({'status': 'settings_updated'})
                    
            except Exception as e:
                logger.error(f"Error in settings: {e}")
                return jsonify({'error': str(e)}), 500
        
        return app

def main():
    """Main function to start the human tracking car system."""
    logger.info("Starting Human Tracking Car System (Non-blocking version)...")
    
    try:
        # Create app wrapper
        app_wrapper = NonBlockingApp()
        
        # Create Flask app immediately
        app = app_wrapper.create_placeholder_app()
        app_wrapper.app = app
        
        # Start component initialization in background
        init_thread = threading.Thread(
            target=app_wrapper.init_components_async,
            daemon=True
        )
        init_thread.start()
        
        # Start web server immediately
        logger.info("Starting web server on http://0.0.0.0:5000")
        logger.info("Components will initialize in the background...")
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
        if hasattr(app_wrapper, 'human_tracker') and app_wrapper.human_tracker:
            app_wrapper.human_tracker.stop_tracking()
        if hasattr(app_wrapper, 'motor_controller') and app_wrapper.motor_controller:
            app_wrapper.motor_controller.cleanup()
        if hasattr(app_wrapper, 'camera_manager') and app_wrapper.camera_manager:
            app_wrapper.camera_manager.cleanup()

if __name__ == "__main__":
    main()