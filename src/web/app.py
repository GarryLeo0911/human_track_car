"""
Flask Web Application
Provides web interface for controlling and monitoring the human tracking car.
"""

from flask import Flask, render_template, Response, jsonify, request
from flask_cors import CORS
import logging
import time
from src.camera.camera_manager import StreamingHandler

logger = logging.getLogger(__name__)

def create_app(human_tracker):
    """
    Create and configure the Flask application.
    
    Args:
        human_tracker: HumanTracker instance (can be None initially)
        
    Returns:
        Configured Flask app
    """
    app = Flask(__name__, 
                template_folder='../../templates',
                static_folder='../../static')
    
    # Enable CORS for cross-origin requests (needed for SOFT3888 integration)
    CORS(app, resources={
        r"/video_feed": {
            "origins": "*",
            "methods": ["GET", "POST", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization", "Access-Control-Allow-Credentials"],
            "supports_credentials": False
        },
        r"/api/*": {
            "origins": "*",
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization", "Access-Control-Allow-Credentials"],
            "supports_credentials": False
        },
        r"/*": {
            "origins": "*",
            "methods": ["GET", "POST", "OPTIONS"],
            "allow_headers": ["Content-Type"],
            "supports_credentials": False
        }
    })
    
    # Store tracker reference (can be None initially)
    app.human_tracker = human_tracker
    
    # Create streaming handler (can be None initially)
    if human_tracker and hasattr(human_tracker, 'camera_manager'):
        app.streaming_handler = StreamingHandler(human_tracker.camera_manager)
    else:
        app.streaming_handler = None
    
    @app.route('/')
    def index():
        """Main control interface."""
        return render_template('index.html')
        
    @app.route('/video_feed')
    def video_feed():
        """Video streaming route with CORS headers."""
        def generate():
            while True:
                try:
                    if app.streaming_handler:
                        # Use real camera stream
                        for frame in app.streaming_handler.generate_mjpeg_stream():
                            yield frame
                            break
                    else:
                        # Generate placeholder frame
                        import cv2
                        import numpy as np
                        
                        frame = np.zeros((480, 640, 3), dtype=np.uint8)
                        cv2.putText(frame, "Initializing camera...", (50, 240), 
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
                    
        response = Response(generate(),
                           mimetype='multipart/x-mixed-replace; boundary=frame')
        
        # Add explicit CORS headers for video stream
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'GET, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
        
        return response
            
    @app.route('/api/status')
    def get_status():
        """Get system status."""
        try:
            if app.human_tracker:
                tracking_status = app.human_tracker.get_tracking_status()
                motor_status = app.human_tracker.motor_controller.get_status()
                camera_status = app.human_tracker.camera_manager.get_status()
            else:
                tracking_status = {'tracking': False, 'last_human_center': None}
                motor_status = {'is_moving': False, 'rpi_mode': False}
                camera_status = {'camera_active': False, 'framerate': 0}
            
            return jsonify({
                'tracking': tracking_status,
                'motor': motor_status,
                'camera': camera_status,
                'components_ready': app.human_tracker is not None,
                'timestamp': time.time()
            })
        except Exception as e:
            logger.error(f"Error getting status: {e}")
            return jsonify({'error': str(e)}), 500
            
    @app.route('/api/control/start', methods=['POST'])
    def start_tracking():
        """Start human tracking."""
        try:
            if not app.human_tracker:
                return jsonify({'error': 'System still initializing, please wait...'}), 503
                
            if not app.human_tracker.tracking:
                # Start tracking in new thread if not already running
                import threading
                tracking_thread = threading.Thread(
                    target=app.human_tracker.start_tracking,
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
            if app.human_tracker:
                app.human_tracker.stop_tracking()
            return jsonify({'status': 'tracking_stopped'})
        except Exception as e:
            logger.error(f"Error stopping tracking: {e}")
            return jsonify({'error': str(e)}), 500
            
    @app.route('/api/control/manual', methods=['POST'])
    def manual_control():
        """Manual motor control."""
        try:
            if not app.human_tracker:
                return jsonify({'error': 'System still initializing, please wait...'}), 503
                
            data = request.get_json()
            
            if not data:
                return jsonify({'error': 'No data provided'}), 400
                
            action = data.get('action')
            speed = data.get('speed', 50)
            
            # Stop tracking for manual control
            app.human_tracker.stop_tracking()
            
            # Execute manual command
            motor_controller = app.human_tracker.motor_controller
            
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
            if request.method == 'GET':
                if app.human_tracker:
                    # Return current settings
                    return jsonify({
                        'target_distance': app.human_tracker.target_distance,
                        'pid_x': {
                            'kp': app.human_tracker.pid_x.kp,
                            'ki': app.human_tracker.pid_x.ki,
                            'kd': app.human_tracker.pid_x.kd
                        },
                        'pid_distance': {
                            'kp': app.human_tracker.pid_distance.kp,
                            'ki': app.human_tracker.pid_distance.ki,
                            'kd': app.human_tracker.pid_distance.kd
                        }
                    })
                else:
                    # Return default settings
                    return jsonify({
                        'target_distance': 150,
                        'pid_x': {'kp': 0.5, 'ki': 0.1, 'kd': 0.2},
                        'pid_distance': {'kp': 0.3, 'ki': 0.05, 'kd': 0.1}
                    })
            else:
                if not app.human_tracker:
                    return jsonify({'error': 'System still initializing, please wait...'}), 503
                    
                # Update settings
                data = request.get_json()
                
                if 'target_distance' in data:
                    app.human_tracker.target_distance = data['target_distance']
                    
                if 'pid_x' in data:
                    pid_data = data['pid_x']
                    app.human_tracker.pid_x.kp = pid_data.get('kp', app.human_tracker.pid_x.kp)
                    app.human_tracker.pid_x.ki = pid_data.get('ki', app.human_tracker.pid_x.ki)
                    app.human_tracker.pid_x.kd = pid_data.get('kd', app.human_tracker.pid_x.kd)
                    
                if 'pid_distance' in data:
                    pid_data = data['pid_distance']
                    app.human_tracker.pid_distance.kp = pid_data.get('kp', app.human_tracker.pid_distance.kp)
                    app.human_tracker.pid_distance.ki = pid_data.get('ki', app.human_tracker.pid_distance.ki)
                    app.human_tracker.pid_distance.kd = pid_data.get('kd', app.human_tracker.pid_distance.kd)
                    
                return jsonify({'status': 'settings_updated'})
                
        except Exception as e:
            logger.error(f"Error in settings: {e}")
            return jsonify({'error': str(e)}), 500
    
    return app