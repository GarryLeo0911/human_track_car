"""
Lightweight Detector Configuration File
"""

# Detector selection configuration
DETECTOR_CONFIGS = {
    # Motion detector - Most lightweight
    'motion': {
        'name': 'Motion Detection',
        'class': 'MotionBasedDetector',
        'description': 'Frame difference based motion detection, most lightweight, suitable for detecting moving people',
        'pros': ['Extremely low CPU usage', 'Real-time performance', 'No model files required'],
        'cons': ['Requires human movement', 'Ineffective for stationary humans', 'Susceptible to environmental interference'],
        'recommended_for': ['Raspberry Pi Zero', 'Ultra low power scenarios', 'Real-time tracking'],
        'memory_usage': '~5MB',
        'cpu_usage': '~10%',
        'detection_time': '~10ms'
    },
    
    # Edge detector - Balanced performance
    'edge': {
        'name': 'Edge Detection',
        'class': 'EdgeBasedDetector',
        'description': 'Canny edge detection based human contour detection',
        'pros': ['Medium CPU usage', 'Effective for stationary humans', 'Good lighting adaptation'],
        'cons': ['False positives in complex backgrounds', 'Requires clear contours', 'Parameters need tuning'],
        'recommended_for': ['Raspberry Pi 3B+', 'Indoor environments', 'Structured scenes'],
        'memory_usage': '~8MB',
        'cpu_usage': '~15%',
        'detection_time': '~20ms'
    },
    
    # Skin color detector - Specific scenarios
    'color': {
        'name': 'Skin Color Detection',
        'class': 'ColorBasedDetector',
        'description': 'HSV-based skin color detection for exposed human skin',
        'pros': ['Sensitive to human features', 'Fast detection', 'Simple and effective'],
        'cons': ['Heavily affected by lighting', 'Requires exposed skin', 'Racial bias'],
        'recommended_for': ['Indoor fixed lighting', 'Close-range detection', 'Specific demographics'],
        'memory_usage': '~6MB',
        'cpu_usage': '~12%',
        'detection_time': '~15ms'
    },
    
    # Background subtraction detector - Improved motion detection
    'background': {
        'name': 'Background Subtraction',
        'class': 'BackgroundSubtractionDetector',
        'description': 'Gaussian mixture model based background subtraction for foreground moving target detection',
        'pros': ['Adaptive background learning', 'Stable detection', 'Strong noise resistance'],
        'cons': ['Requires initialization time', 'Sensitive to background changes', 'Poor stationary human detection'],
        'recommended_for': ['Fixed camera position', 'Indoor monitoring', 'Long-term operation'],
        'memory_usage': '~12MB',
        'cpu_usage': '~18%',
        'detection_time': '~25ms'
    },
    
    # Hybrid detector - Best results
    'hybrid': {
        'name': 'Hybrid Detection',
        'class': 'HybridDetector',
        'description': 'Combination of multiple detection methods to improve detection stability',
        'pros': ['High detection stability', 'Strong adaptability', 'Low false positive rate'],
        'cons': ['Higher CPU usage', 'Increased complexity', 'Slightly higher latency'],
        'recommended_for': ['Raspberry Pi 4', 'Critical applications', 'High reliability requirements'],
        'memory_usage': '~20MB',
        'cpu_usage': '~25%',
        'detection_time': '~35ms'
    }
}

# Default detector selection
DEFAULT_DETECTOR = 'motion'

# Platform-based recommendations
PLATFORM_RECOMMENDATIONS = {
    'raspberry_pi_zero': {
        'recommended': 'motion',
        'alternatives': ['color'],
        'avoid': ['edge', 'background', 'hybrid']
    },
    'raspberry_pi_3': {
        'recommended': 'edge',
        'alternatives': ['motion', 'color'],
        'avoid': ['hybrid']
    },
    'raspberry_pi_4': {
        'recommended': 'background',
        'alternatives': ['edge', 'hybrid'],
        'avoid': []
    },
    'other': {
        'recommended': 'motion',
        'alternatives': ['edge', 'color'],
        'avoid': ['hybrid']
    }
}

# Scenario recommendations
SCENARIO_RECOMMENDATIONS = {
    'indoor_tracking': {
        'recommended': 'background',
        'alternatives': ['motion', 'edge']
    },
    'outdoor_tracking': {
        'recommended': 'motion',
        'alternatives': ['edge']
    },
    'real_time_following': {
        'recommended': 'motion',
        'alternatives': ['color']
    },
    'security_monitoring': {
        'recommended': 'background',
        'alternatives': ['hybrid', 'edge']
    },
    'demo_showcase': {
        'recommended': 'edge',
        'alternatives': ['background', 'hybrid']
    }
}

# Performance target configuration
PERFORMANCE_TARGETS = {
    'ultra_low_power': {
        'max_cpu_usage': 15,
        'max_memory': 10,
        'max_detection_time': 20,
        'recommended': 'motion'
    },
    'balanced': {
        'max_cpu_usage': 25,
        'max_memory': 20,
        'max_detection_time': 30,
        'recommended': 'edge'
    },
    'high_accuracy': {
        'max_cpu_usage': 35,
        'max_memory': 30,
        'max_detection_time': 40,
        'recommended': 'background'
    }
}

def get_detector_config(detector_type):
    """Get configuration for specified detector"""
    return DETECTOR_CONFIGS.get(detector_type, DETECTOR_CONFIGS[DEFAULT_DETECTOR])

def get_platform_recommendation(platform='other'):
    """Get recommended detector based on hardware platform"""
    return PLATFORM_RECOMMENDATIONS.get(platform, PLATFORM_RECOMMENDATIONS['other'])

def get_scenario_recommendation(scenario):
    """Get recommended detector based on application scenario"""
    return SCENARIO_RECOMMENDATIONS.get(scenario, {'recommended': DEFAULT_DETECTOR, 'alternatives': []})

def get_performance_recommendation(target='balanced'):
    """Get recommended detector based on performance target"""
    return PERFORMANCE_TARGETS.get(target, PERFORMANCE_TARGETS['balanced'])

def print_detector_info(detector_type):
    """Print detailed information for specified detector"""
    config = get_detector_config(detector_type)
    
    print(f"\n=== {config['name']} Detector ===")
    print(f"Description: {config['description']}")
    print(f"Memory Usage: {config['memory_usage']}")
    print(f"CPU Usage: {config['cpu_usage']}")
    print(f"Detection Time: {config['detection_time']}")
    
    print("\nAdvantages:")
    for pro in config['pros']:
        print(f"  + {pro}")
    
    print("\nDisadvantages:")
    for con in config['cons']:
        print(f"  - {con}")
    
    print("\nRecommended Scenarios:")
    for rec in config['recommended_for']:
        print(f"  * {rec}")

def recommend_detector(platform=None, scenario=None, performance_target=None):
    """Intelligent detector recommendation"""
    recommendations = {}
    
    if platform:
        platform_rec = get_platform_recommendation(platform)
        recommendations['platform'] = platform_rec['recommended']
    
    if scenario:
        scenario_rec = get_scenario_recommendation(scenario)
        recommendations['scenario'] = scenario_rec['recommended']
    
    if performance_target:
        performance_rec = get_performance_recommendation(performance_target)
        recommendations['performance'] = performance_rec['recommended']
    
    # Comprehensive recommendation (simple voting mechanism)
    if recommendations:
        detector_votes = {}
        for rec in recommendations.values():
            detector_votes[rec] = detector_votes.get(rec, 0) + 1
        
        # Select the one with most votes
        final_recommendation = max(detector_votes.keys(), key=lambda x: detector_votes[x])
    else:
        final_recommendation = DEFAULT_DETECTOR
    
    return final_recommendation, recommendations

if __name__ == "__main__":
    # Usage example
    print("Lightweight Detector Configuration Guide")
    print("=" * 40)
    
    # Display all available detectors
    print("\nAvailable Detectors:")
    for detector_type in DETECTOR_CONFIGS:
        config = DETECTOR_CONFIGS[detector_type]
        print(f"  {detector_type}: {config['name']} - {config['description']}")
    
    # Example recommendations
    print("\nExample Recommendations:")
    
    # Raspberry Pi Zero scenario
    rec, details = recommend_detector(platform='raspberry_pi_zero', scenario='real_time_following')
    print(f"\nRaspberry Pi Zero Real-time Tracking Recommendation: {rec}")
    print(f"Recommendation Details: {details}")
    
    # Raspberry Pi 4 indoor monitoring
    rec, details = recommend_detector(platform='raspberry_pi_4', scenario='indoor_tracking')
    print(f"\nRaspberry Pi 4 Indoor Tracking Recommendation: {rec}")
    print(f"Recommendation Details: {details}")
    
    # Ultra low power target
    rec, details = recommend_detector(performance_target='ultra_low_power')
    print(f"\nUltra Low Power Target Recommendation: {rec}")
    print(f"Recommendation Details: {details}")
    
    # Detailed information example
    print_detector_info('motion')