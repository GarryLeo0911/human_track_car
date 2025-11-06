"""
Ultrasonic Distance Sensor Module
Based on Freenove official implementation with tracking optimizations.
"""

import time
import logging
import threading
from typing import Optional, List, Tuple
from threading import Lock

logger = logging.getLogger(__name__)

# Try to import required modules for Raspberry Pi
try:
    from gpiozero import DistanceSensor, PWMSoftwareFallback, DistanceSensorNoEcho
    import warnings
    ULTRASONIC_AVAILABLE = True
except ImportError:
    ULTRASONIC_AVAILABLE = False
    logger.warning("gpiozero not available - running in simulation mode")


class UltrasonicSensor:
    """
    Ultrasonic distance sensor based on Freenove official implementation.
    Enhanced for human tracking with continuous monitoring and averaging.
    """
    
    def __init__(self, trigger_pin: int = 27, echo_pin: int = 22, max_distance: float = 3.0):
        """
        Initialize the ultrasonic sensor.
        
        Args:
            trigger_pin: GPIO pin for trigger (default: 27)
            echo_pin: GPIO pin for echo (default: 22)
            max_distance: Maximum detection distance in meters (default: 3.0)
        """
        self.trigger_pin = trigger_pin
        self.echo_pin = echo_pin
        self.max_distance = max_distance
        self.simulation_mode = not ULTRASONIC_AVAILABLE
        
        # Distance tracking for human tracking
        self.current_distance = None
        self.distance_history = []
        self.history_length = 5
        self.lock = Lock()
        
        # Continuous monitoring
        self.monitoring = False
        self.monitor_thread = None
        self.monitor_interval = 0.1  # 100ms between readings
        
        if not self.simulation_mode:
            try:
                # Suppress warnings as in official code
                warnings.filterwarnings("ignore", category=DistanceSensorNoEcho)
                warnings.filterwarnings("ignore", category=PWMSoftwareFallback)
                
                # Initialize sensor as in official code
                self.sensor = DistanceSensor(
                    echo=self.echo_pin,
                    trigger=self.trigger_pin,
                    max_distance=self.max_distance
                )
                logger.info(f"Ultrasonic sensor initialized on pins {trigger_pin}/{echo_pin}")
            except Exception as e:
                logger.error(f"Failed to initialize ultrasonic sensor: {e}")
                self.simulation_mode = True
        
        if self.simulation_mode:
            logger.info("Ultrasonic sensor running in simulation mode")
    
    def get_distance(self) -> Optional[float]:
        """
        Get single distance measurement.
        
        Returns:
            Distance in centimeters, or None if reading failed
        """
        if self.simulation_mode:
            # Simulate distance readings for testing
            import random
            return round(random.uniform(50, 200), 1)
        
        try:
            # Official implementation: distance * 100 for cm
            distance = self.sensor.distance * 100
            return round(float(distance), 1)
        except RuntimeWarning as e:
            logger.warning(f"Ultrasonic reading warning: {e}")
            return None
        except Exception as e:
            logger.error(f"Ultrasonic reading error: {e}")
            return None
    
    def get_averaged_distance(self, samples: int = 3) -> Optional[float]:
        """
        Get averaged distance over multiple readings for stability.
        
        Args:
            samples: Number of samples to average
            
        Returns:
            Averaged distance in centimeters
        """
        readings = []
        for _ in range(samples):
            distance = self.get_distance()
            if distance is not None:
                readings.append(distance)
            time.sleep(0.02)  # Small delay between readings
        
        if readings:
            return round(sum(readings) / len(readings), 1)
        return None
    
    def start_continuous_monitoring(self):
        """Start continuous distance monitoring in background thread."""
        if self.monitoring:
            return
        
        self.monitoring = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
        logger.info("Ultrasonic continuous monitoring started")
    
    def stop_continuous_monitoring(self):
        """Stop continuous distance monitoring."""
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=1.0)
        logger.info("Ultrasonic continuous monitoring stopped")
    
    def _monitor_loop(self):
        """Background monitoring loop."""
        while self.monitoring:
            try:
                distance = self.get_distance()
                
                if distance is not None:
                    with self.lock:
                        self.current_distance = distance
                        
                        # Update history for averaging
                        self.distance_history.append(distance)
                        if len(self.distance_history) > self.history_length:
                            self.distance_history.pop(0)
                
                time.sleep(self.monitor_interval)
                
            except Exception as e:
                logger.error(f"Error in ultrasonic monitoring: {e}")
                time.sleep(0.5)  # Longer delay on error
    
    def get_current_distance(self) -> Optional[float]:
        """
        Get the most recent distance reading from continuous monitoring.
        
        Returns:
            Current distance in centimeters, or None if no recent reading
        """
        with self.lock:
            return self.current_distance
    
    def get_smoothed_distance(self) -> Optional[float]:
        """
        Get smoothed distance from history buffer.
        
        Returns:
            Averaged distance over recent readings
        """
        with self.lock:
            if len(self.distance_history) >= 2:
                return round(sum(self.distance_history) / len(self.distance_history), 1)
            return self.current_distance
    
    def get_distance_stats(self) -> dict:
        """
        Get detailed distance statistics.
        
        Returns:
            Dictionary with distance statistics
        """
        with self.lock:
            if not self.distance_history:
                return {
                    'current': self.current_distance,
                    'average': None,
                    'min': None,
                    'max': None,
                    'samples': 0
                }
            
            return {
                'current': self.current_distance,
                'average': round(sum(self.distance_history) / len(self.distance_history), 1),
                'min': min(self.distance_history),
                'max': max(self.distance_history),
                'samples': len(self.distance_history)
            }
    
    def is_object_in_range(self, min_distance: float = 20, max_distance: float = 300) -> bool:
        """
        Check if an object is detected within specified range.
        
        Args:
            min_distance: Minimum distance in cm
            max_distance: Maximum distance in cm
            
        Returns:
            True if object detected in range
        """
        distance = self.get_smoothed_distance()
        if distance is None:
            return False
        return min_distance <= distance <= max_distance
    
    def get_status(self) -> dict:
        """Get sensor status information."""
        stats = self.get_distance_stats()
        return {
            'hardware_available': not self.simulation_mode,
            'monitoring': self.monitoring,
            'trigger_pin': self.trigger_pin,
            'echo_pin': self.echo_pin,
            'max_distance': self.max_distance,
            **stats
        }
    
    def close(self):
        """Close the ultrasonic sensor and cleanup resources."""
        self.stop_continuous_monitoring()
        
        if not self.simulation_mode and hasattr(self, 'sensor'):
            try:
                self.sensor.close()
                logger.info("Ultrasonic sensor closed")
            except Exception as e:
                logger.error(f"Error closing ultrasonic sensor: {e}")
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_value, traceback):
        """Context manager exit."""
        self.close()


# Test the ultrasonic sensor
if __name__ == '__main__':
    print("Testing Ultrasonic Sensor (Freenove-compatible)")
    print("=" * 50)
    
    with UltrasonicSensor() as ultrasonic:
        try:
            print("Starting continuous monitoring...")
            ultrasonic.start_continuous_monitoring()
            
            print("Press Ctrl+C to stop")
            while True:
                # Get current distance
                distance = ultrasonic.get_smoothed_distance()
                
                # Get detailed stats
                stats = ultrasonic.get_distance_stats()
                
                if distance is not None:
                    print(f"Distance: {distance:6.1f}cm | "
                          f"Avg: {stats['average']:6.1f}cm | "
                          f"Range: {stats['min']:5.1f}-{stats['max']:5.1f}cm | "
                          f"Samples: {stats['samples']}")
                    
                    # Test object detection
                    if ultrasonic.is_object_in_range(30, 200):
                        print("  → Object detected in tracking range!")
                else:
                    print("No distance reading available")
                
                time.sleep(0.5)
                
        except KeyboardInterrupt:
            print("\nTest ended by user")
        except Exception as e:
            print(f"Test error: {e}")
            import traceback
            traceback.print_exc()