# Testing and Demo Scripts

This directory contains testing, demonstration, and validation scripts for the human tracking car project.

## Core Tests

- **`test_enhanced_detection.py`** - Compare different detection methods with performance metrics
- **`test_enhanced_tracking.py`** - Test advanced tracking algorithms and motion control
- **`test_lightweight_detectors.py`** - Test lightweight detection options for resource-constrained devices

## Hardware Tests

- **`test_motor_directions.py`** - Verify motor directions and movement accuracy
- **`test_ultrasonic_integration.py`** - Test ultrasonic sensor integration and obstacle avoidance

## Demonstrations

- **`demo_enhanced_detection.py`** - Interactive demo showcasing all detection methods side-by-side

## Usage

Run any test directly:

```bash
# Test detection methods
python tests/test_enhanced_detection.py

# Test tracking performance
python tests/test_enhanced_tracking.py

# Test hardware components
python tests/test_motor_directions.py

# Interactive demo
python tests/demo_enhanced_detection.py
```

All tests include detailed logging and performance metrics to help with debugging and optimization.