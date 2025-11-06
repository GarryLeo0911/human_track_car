"""
Test the Freenove motor controller integration
"""

import sys
import time
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def test_freenove_motor():
    """Test the Freenove motor controller."""
    print("Testing Freenove Motor Controller")
    print("=" * 40)
    
    try:
        from src.control.freenove_motor_controller import FreenoveMotorController
        
        motor = FreenoveMotorController()
        print(f"✅ Motor controller initialized")
        print(f"   Hardware available: {motor.hardware_available}")
        
        # Test basic movements
        print("\n🚗 Testing basic movements:")
        
        print("  Forward...")
        motor.move_forward(50)
        time.sleep(0.5)
        
        print("  Backward...")
        motor.move_backward(50)
        time.sleep(0.5)
        
        print("  Left...")
        motor.turn_left(50)
        time.sleep(0.5)
        
        print("  Right...")
        motor.turn_right(50)
        time.sleep(0.5)
        
        print("  Combined (forward + slight right)...")
        motor.move_with_turn(30, 15)
        time.sleep(0.5)
        
        print("  Stop...")
        motor.stop()
        
        # Test status
        status = motor.get_status()
        print(f"\n📊 Motor status: {status}")
        
        motor.cleanup()
        print("\n✅ Freenove motor controller test completed!")
        return True
        
    except Exception as e:
        print(f"\n❌ Error testing motor controller: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_app_startup():
    """Test if the app can start with Freenove motor controller."""
    print("\n" + "=" * 40)
    print("Testing App Startup with Freenove Motors")
    print("=" * 40)
    
    try:
        # Import main components
        from src.control.freenove_motor_controller import FreenoveMotorController
        from src.camera.camera_manager import CameraManager
        from src.tracking.human_tracker import HumanTracker
        
        print("✅ All imports successful")
        
        # Test component initialization
        print("🔧 Initializing motor controller...")
        motor = FreenoveMotorController()
        print(f"   Motor ready: {motor.hardware_available}")
        
        print("📹 Initializing camera manager...")
        camera = CameraManager()
        print(f"   Camera ready: {camera.camera_active}")
        
        print("🎯 Initializing human tracker...")
        tracker = HumanTracker(camera, motor)
        print("   Tracker ready")
        
        # Cleanup
        tracker.stop_tracking()
        motor.cleanup()
        camera.cleanup()
        
        print("\n✅ All components work together!")
        return True
        
    except Exception as e:
        print(f"\n❌ Error testing app startup: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main test function."""
    print("Human Tracking Car - Freenove Integration Test")
    print("=" * 50)
    
    # Test motor controller
    motor_ok = test_freenove_motor()
    
    # Test app startup
    app_ok = test_app_startup()
    
    print("\n" + "=" * 50)
    print("TEST SUMMARY:")
    print(f"Motor Controller: {'✅ PASS' if motor_ok else '❌ FAIL'}")
    print(f"App Integration:  {'✅ PASS' if app_ok else '❌ FAIL'}")
    
    if motor_ok and app_ok:
        print("\n🎉 All tests passed! You can now run:")
        print("   python main.py")
        print("\nThe motor controller will:")
        print("   • Work in simulation mode on Windows")
        print("   • Use real Freenove hardware on Raspberry Pi")
        print("   • Show motor commands in the terminal")
    else:
        print("\n⚠️  Some tests failed. Check the errors above.")
    
    return motor_ok and app_ok

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)