"""
Camera Management Module
Handles camera operations and video streaming.
"""

import cv2
import numpy as np
import threading
import logging
import time
from threading import Lock
import base64

# Try to import camera modules (Ubuntu vs Raspberry Pi OS compatibility)
PI_CAMERA_AVAILABLE = False
PICAMERA2_AVAILABLE = False

# Try picamera2 first (better Ubuntu support)
try:
    from picamera2 import Picamera2
    PICAMERA2_AVAILABLE = True
    CAMERA_LIB = 'picamera2'
except ImportError:
    # Fallback to original picamera
    try:
        from picamera import PiCamera
        from picamera.array import PiRGBArray
        PI_CAMERA_AVAILABLE = True
        CAMERA_LIB = 'picamera'
    except ImportError:
        CAMERA_LIB = 'opencv'

if not (PI_CAMERA_AVAILABLE or PICAMERA2_AVAILABLE):
    logging.warning(f"Pi Camera modules not available. Using OpenCV camera. Available: {CAMERA_LIB}")

logger = logging.getLogger(__name__)

class CameraManager:
    """Manages camera operations and frame processing."""
    
    def __init__(self, resolution: tuple = (640, 480), framerate: int = 30):
        """
        Initialize camera manager.
        
        Args:
            resolution: Camera resolution (width, height)
            framerate: Target framerate
        """
        self.resolution = resolution
        self.framerate = framerate
        self.lock = Lock()
        
        # Frame storage
        self.current_frame = None
        self.processed_frame = None
        self.frame_count = 0
        
        # Camera state
        self.camera_active = False
        self.use_pi_camera = PICAMERA2_AVAILABLE or PI_CAMERA_AVAILABLE
        self.camera_lib = CAMERA_LIB
        
        # Initialize camera
        self._init_camera()
        
    def _init_camera(self):
        """Initialize the camera system."""
        try:
            if self.use_pi_camera:
                if PICAMERA2_AVAILABLE:
                    self._init_picamera2()
                elif PI_CAMERA_AVAILABLE:
                    self._init_pi_camera()
            else:
                self._init_usb_camera()
                
            # Start capture thread
            self.capture_thread = threading.Thread(
                target=self._capture_loop,
                daemon=True
            )
            self.capture_thread.start()
            
            logger.info(f"Camera initialized - Library: {self.camera_lib}")
            
        except Exception as e:
            logger.error(f"Failed to initialize camera: {e}")
            self.camera_active = False
            
            
    def _init_picamera2(self):
        """Initialize Raspberry Pi camera using picamera2 (Ubuntu compatible)."""
        try:
            self.camera = Picamera2()
            
            # Configure camera for video capture
            config = self.camera.create_video_configuration(
                main={"size": self.resolution, "format": "RGB888"}
            )
            self.camera.configure(config)
            
            # Start camera
            self.camera.start()
            
            # Allow camera to warm up
            time.sleep(2)
            
            self.camera_active = True
            logger.info("PiCamera2 initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize PiCamera2: {e}")
            self.use_pi_camera = False
            self._init_usb_camera()
            
    def _init_pi_camera(self):
        """Initialize Raspberry Pi camera."""
        try:
            self.camera = PiCamera()
            self.camera.resolution = self.resolution
            self.camera.framerate = self.framerate
            
            # Allow camera to warm up
            time.sleep(2)
            
            # Initialize capture array
            self.raw_capture = PiRGBArray(self.camera, size=self.resolution)
            
            self.camera_active = True
            logger.info("Pi Camera initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Pi Camera: {e}")
            self.use_pi_camera = False
            self._init_usb_camera()
            
    def _init_usb_camera(self):
        """Initialize USB/webcam camera."""
        try:
            # Try different camera indices
            for camera_index in range(3):
                self.camera = cv2.VideoCapture(camera_index)
                if self.camera.isOpened():
                    break
            else:
                raise Exception("No camera found")
                
            # Set camera properties
            self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, self.resolution[0])
            self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, self.resolution[1])
            self.camera.set(cv2.CAP_PROP_FPS, self.framerate)
            
            # Test capture
            ret, frame = self.camera.read()
            if not ret:
                raise Exception("Failed to capture test frame")
                
            self.camera_active = True
            logger.info("USB Camera initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize USB camera: {e}")
            self.camera_active = False
            
    def _capture_loop(self):
        """Main camera capture loop."""
        logger.info("Starting camera capture loop")
        
        while self.camera_active:
            try:
                if self.use_pi_camera:
                    if PICAMERA2_AVAILABLE:
                        self._capture_picamera2_frame()
                    elif PI_CAMERA_AVAILABLE:
                        self._capture_pi_frame()
                else:
                    self._capture_usb_frame()
                    
                self.frame_count += 1
                
                # Control frame rate
                time.sleep(1.0 / self.framerate)
                
            except Exception as e:
                logger.error(f"Error in capture loop: {e}")
                time.sleep(0.1)
                
    def _capture_picamera2_frame(self):
        """Capture frame from Pi camera using picamera2."""
        try:
            frame = self.camera.capture_array()
            
            # Convert RGB to BGR for OpenCV compatibility
            frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
            
            with self.lock:
                self.current_frame = frame
                
        except Exception as e:
            logger.error(f"Error capturing picamera2 frame: {e}")
                
    def _capture_pi_frame(self):
        """Capture frame from Pi camera."""
        try:
            self.raw_capture.truncate(0)
            self.camera.capture(self.raw_capture, format="bgr", use_video_port=True)
            frame = self.raw_capture.array.copy()
            
            with self.lock:
                self.current_frame = frame
                
        except Exception as e:
            logger.error(f"Error capturing Pi camera frame: {e}")
            
    def _capture_usb_frame(self):
        """Capture frame from USB camera."""
        try:
            ret, frame = self.camera.read()
            if ret:
                with self.lock:
                    self.current_frame = frame
            else:
                logger.warning("Failed to read frame from USB camera")
                
        except Exception as e:
            logger.error(f"Error capturing USB camera frame: {e}")
            
    def get_frame(self) -> np.ndarray:
        """
        Get the current frame.
        
        Returns:
            Current camera frame or None if not available
        """
        with self.lock:
            return self.current_frame.copy() if self.current_frame is not None else None
            
    def set_processed_frame(self, frame: np.ndarray):
        """
        Set the processed frame (with detections, etc.).
        
        Args:
            frame: Processed frame to store
        """
        with self.lock:
            self.processed_frame = frame.copy() if frame is not None else None
            
    def get_processed_frame(self) -> np.ndarray:
        """
        Get the processed frame.
        
        Returns:
            Processed frame or current frame if no processed frame available
        """
        with self.lock:
            if self.processed_frame is not None:
                return self.processed_frame.copy()
            elif self.current_frame is not None:
                return self.current_frame.copy()
            else:
                return None
                
    def get_frame_as_jpeg(self, use_processed: bool = True) -> bytes:
        """
        Get frame encoded as JPEG bytes.
        
        Args:
            use_processed: Whether to use processed frame or raw frame
            
        Returns:
            JPEG encoded frame bytes
        """
        try:
            frame = self.get_processed_frame() if use_processed else self.get_frame()
            
            if frame is None:
                # Return blank frame
                frame = np.zeros((480, 640, 3), dtype=np.uint8)
                cv2.putText(frame, "No Camera", (50, 50), 
                           cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
                           
            # Encode as JPEG
            ret, buffer = cv2.imencode('.jpg', frame, 
                                     [cv2.IMWRITE_JPEG_QUALITY, 85])
            
            if ret:
                return buffer.tobytes()
            else:
                return b''
                
        except Exception as e:
            logger.error(f"Error encoding frame as JPEG: {e}")
            return b''
            
    def get_frame_as_base64(self, use_processed: bool = True) -> str:
        """
        Get frame encoded as base64 string.
        
        Args:
            use_processed: Whether to use processed frame or raw frame
            
        Returns:
            Base64 encoded frame string
        """
        try:
            jpeg_bytes = self.get_frame_as_jpeg(use_processed)
            if jpeg_bytes:
                return base64.b64encode(jpeg_bytes).decode('utf-8')
            else:
                return ""
                
        except Exception as e:
            logger.error(f"Error encoding frame as base64: {e}")
            return ""
            
    def get_status(self) -> dict:
        """Get camera status information."""
        return {
            'camera_active': self.camera_active,
            'use_pi_camera': self.use_pi_camera,
            'resolution': self.resolution,
            'framerate': self.framerate,
            'frame_count': self.frame_count,
            'has_current_frame': self.current_frame is not None,
            'has_processed_frame': self.processed_frame is not None
        }
        
    def cleanup(self):
        """Clean up camera resources."""
        logger.info("Cleaning up camera...")
        self.camera_active = False
        
        # Wait for capture thread to finish
        if hasattr(self, 'capture_thread'):
            self.capture_thread.join(timeout=2)
            
        # Release camera
        try:
            if self.use_pi_camera and hasattr(self, 'camera'):
                if PICAMERA2_AVAILABLE:
                    self.camera.stop()
                    self.camera.close()
                elif PI_CAMERA_AVAILABLE:
                    self.camera.close()
            elif hasattr(self, 'camera'):
                self.camera.release()
        except Exception as e:
            logger.error(f"Error releasing camera: {e}")
            
        logger.info("Camera cleanup completed")


class StreamingHandler:
    """Handles video streaming for web interface."""
    
    def __init__(self, camera_manager: CameraManager):
        """
        Initialize streaming handler.
        
        Args:
            camera_manager: CameraManager instance
        """
        self.camera_manager = camera_manager
        
    def generate_mjpeg_stream(self):
        """
        Generate MJPEG stream for web interface.
        
        Yields:
            MJPEG frame data
        """
        while True:
            try:
                # Get frame as JPEG
                frame_bytes = self.camera_manager.get_frame_as_jpeg(use_processed=True)
                
                if frame_bytes:
                    # Yield frame in MJPEG format
                    yield (b'--frame\r\n'
                           b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
                else:
                    # Send blank frame if no camera data
                    time.sleep(0.1)
                    
            except Exception as e:
                logger.error(f"Error in MJPEG stream: {e}")
                time.sleep(0.1)