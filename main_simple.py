"""
Simplified version of main.py for debugging
"""

from flask import Flask, render_template, Response, jsonify, request
import cv2
import logging
import threading
import time

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

class SimpleCamera:
    """Simple camera class for testing."""
    
    def __init__(self):
        self.camera = None
        self.frame = None
        self.active = False
        self.init_camera()
        
    def init_camera(self):
        """Initialize camera."""
        try:
            logger.info("Initializing camera...")
            
            # Try to open camera
            for i in range(3):
                logger.info(f"Trying camera index {i}")
                self.camera = cv2.VideoCapture(i)
                if self.camera.isOpened():
                    logger.info(f"Camera {i} opened successfully")
                    break
                else:
                    self.camera.release()
            else:
                logger.warning("No camera found, using dummy frame")
                self.camera = None
                
            self.active = True
            logger.info("Camera initialization completed")
            
        except Exception as e:
            logger.error(f"Camera initialization failed: {e}")
            self.camera = None
            self.active = True  # Continue without camera
            
    def get_frame(self):
        """Get current frame."""
        if self.camera and self.camera.isOpened():
            ret, frame = self.camera.read()
            if ret:
                return frame
                
        # Return dummy frame if no camera
        import numpy as np
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        cv2.putText(frame, "No Camera Available", (50, 240), 
                   cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
        return frame
        
    def get_jpeg(self):
        """Get frame as JPEG bytes."""
        frame = self.get_frame()
        ret, buffer = cv2.imencode('.jpg', frame)
        return buffer.tobytes() if ret else b''
        
    def cleanup(self):
        """Clean up camera."""
        self.active = False
        if self.camera:
            self.camera.release()

# Global camera instance
camera = SimpleCamera()

def create_simple_app():
    """Create simplified Flask app."""
    app = Flask(__name__, 
                template_folder='templates',
                static_folder='static')
    
    @app.route('/')
    def index():
        """Main page."""
        logger.info("Index page requested")
        return render_template('index.html')
        
    @app.route('/video_feed')
    def video_feed():
        """Video streaming route."""
        logger.info("Video feed requested")
        
        def generate():
            while True:
                try:
                    frame_bytes = camera.get_jpeg()
                    yield (b'--frame\r\n'
                           b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
                    time.sleep(0.1)  # Control frame rate
                except Exception as e:
                    logger.error(f"Error in video stream: {e}")
                    break
        
        return Response(generate(),
                       mimetype='multipart/x-mixed-replace; boundary=frame')
        
    @app.route('/api/status')
    def get_status():
        """Get system status."""
        logger.info("Status requested")
        return jsonify({
            'camera': {'camera_active': camera.active},
            'motor': {'is_moving': False},
            'tracking': {
                'tracking': False,
                'last_human_center': None
            },
            'timestamp': time.time()
        })
        
    @app.route('/api/control/start', methods=['POST'])
    def start_tracking():
        """Start tracking (dummy)."""
        logger.info("Start tracking requested")
        return jsonify({'status': 'tracking_started'})
        
    @app.route('/api/control/stop', methods=['POST'])
    def stop_tracking():
        """Stop tracking (dummy)."""
        logger.info("Stop tracking requested")
        return jsonify({'status': 'tracking_stopped'})
        
    @app.route('/api/control/manual', methods=['POST'])
    def manual_control():
        """Manual control (dummy)."""
        logger.info("Manual control requested")
        return jsonify({'status': 'executed'})
        
    @app.route('/api/settings', methods=['GET', 'POST'])
    def settings():
        """Settings (dummy)."""
        logger.info("Settings requested")
        if request.method == 'GET':
            return jsonify({
                'target_distance': 150,
                'pid_x': {'kp': 0.5, 'ki': 0.1, 'kd': 0.2},
                'pid_distance': {'kp': 0.3, 'ki': 0.05, 'kd': 0.1}
            })
        else:
            return jsonify({'status': 'settings_updated'})
    
    return app

def main():
    """Main function."""
    logger.info("Starting simplified Human Tracking Car...")
    
    try:
        # Create Flask app
        app = create_simple_app()
        
        # Start web server
        logger.info("Starting web server on http://0.0.0.0:5000")
        logger.info("Access the interface at:")
        logger.info("  - http://127.0.0.1:5000")
        logger.info("  - http://localhost:5000")
        
        app.run(host='0.0.0.0', port=5000, debug=True, threaded=True)
        
    except KeyboardInterrupt:
        logger.info("Shutting down...")
    except Exception as e:
        logger.error(f"Error starting application: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Cleanup
        camera.cleanup()

if __name__ == "__main__":
    main()