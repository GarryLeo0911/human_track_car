"""
Enhanced Lightweight Detector Configuration File
Including improved accuracy detectors
"""

# Detector selection configuration
DETECTOR_CONFIGS = {
    # Motion detector - Most lightweight
    'motion': {
        'name': 'Basic Motion Detection',
        'class': 'MotionBasedDetector',
        'description': 'Frame difference based motion detection, most lightweight, suitable for detecting moving people',
        'pros': ['Extremely low CPU usage', 'Real-time performance', 'No model files required'],
        'cons': ['Requires human movement', 'Ineffective for stationary humans', 'Susceptible to environmental interference'],
        'recommended_for': ['Raspberry Pi Zero', 'Ultra low power scenarios', 'Real-time tracking'],
        'memory_usage': '~5MB',
        'cpu_usage': '~10%',
        'detection_time': '~10ms',
        'accuracy': 'Low'
    },
    
    # Enhanced motion detector - Better accuracy
    'enhanced_motion': {
        'name': 'Enhanced Motion Detection',
        'class': 'EnhancedMotionDetector',
        'description': 'Advanced background subtraction with human shape validation and multi-frame consensus',
        'pros': ['Better human shape recognition', 'Temporal validation', 'Reduced false positives', 'Confidence scoring'],
        'cons': ['Higher CPU usage than basic motion', 'Requires initialization period', 'More memory usage'],
        'recommended_for': ['Raspberry Pi 3B+', 'Raspberry Pi 4', 'When accuracy matters more than speed'],
        'memory_usage': '~15MB',
        'cpu_usage': '~25%',
        'detection_time': '~25ms',
        'accuracy': 'Medium-High'
    },
    
    # Edge detector - Balanced performance
    'edge': {
        'name': 'Basic Edge Detection',
        'class': 'EdgeBasedDetector',
        'description': 'Canny edge detection based human contour detection',
        'pros': ['Medium CPU usage', 'Effective for stationary humans', 'Good lighting adaptation'],
        'cons': ['False positives in complex backgrounds', 'Requires clear contours', 'Parameters need tuning'],
        'recommended_for': ['Raspberry Pi 3B+', 'Indoor environments', 'Structured scenes'],
        'memory_usage': '~8MB',
        'cpu_usage': '~15%',
        'detection_time': '~20ms',
        'accuracy': 'Medium'
    },
    
    # Enhanced edge detector - Better shape analysis
    'enhanced_edge': {
        'name': 'Enhanced Edge Detection',
        'class': 'EnhancedEdgeDetector',
        'description': 'Multi-scale edge detection with sophisticated shape analysis and human proportion validation',
        'pros': ['Better shape recognition', 'Human proportion analysis', 'Multi-scale detection', 'Confidence scoring'],
        'cons': ['Higher computational cost', 'May miss very blurred humans', 'Sensitive to lighting changes'],
        'recommended_for': ['Raspberry Pi 3B+', 'Raspberry Pi 4', 'High-accuracy applications'],
        'memory_usage': '~12MB',
        'cpu_usage': '~30%',
        'detection_time': '~35ms',
        'accuracy': 'High'
    },
    
    # Hybrid detector - Best accuracy
    'hybrid': {
        'name': 'Hybrid Detection (Motion + Edge)',
        'class': 'HybridHumanDetector',
        'description': 'Combines enhanced motion and edge detection for maximum accuracy and reliability',
        'pros': ['Highest accuracy', 'Robust to different conditions', 'Multi-method consensus', 'Best false positive reduction'],
        'cons': ['Highest resource usage', 'Slowest detection', 'Complex parameter tuning'],
        'recommended_for': ['Raspberry Pi 4', 'Critical applications', 'When maximum accuracy is required'],
        'memory_usage': '~25MB',
        'cpu_usage': '~45%',
        'detection_time': '~50ms',
        'accuracy': 'Very High'
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
    
    # Color detector - Skin tone based
    'color': {
        'name': 'Skin Color Detection',
        'class': 'ColorBasedDetector',
        'description': 'Skin tone HSV color space detection, good for detecting people wearing short sleeves',
        'pros': ['Fast processing', 'Good for skin detection', 'Low computational cost'],
        'cons': ['Lighting dependent', 'Ethnicity bias', 'Clothing dependent', 'False positives with similar colors'],
        'recommended_for': ['Controlled lighting', 'Close-range detection', 'Skin exposure scenarios'],
        'memory_usage': '~6MB',
        'cpu_usage': '~12%',
        'detection_time': '~15ms',
        'accuracy': 'Medium'
    }
}

# Default detector selection (enhanced motion for better accuracy)
DEFAULT_DETECTOR = 'enhanced_motion'

# Platform-based recommendations with enhanced detectors
PLATFORM_RECOMMENDATIONS = {
    'raspberry_pi_zero': {
        'recommended': 'motion',
        'alternatives': ['color'],
        'avoid': ['enhanced_motion', 'enhanced_edge', 'hybrid'],
        'reason': 'Limited CPU and memory, requires most lightweight options'
    },
    'raspberry_pi_3': {
        'recommended': 'enhanced_motion',
        'alternatives': ['motion', 'edge', 'color'],
        'avoid': ['hybrid'],
        'reason': 'Good balance of performance and accuracy'
    },
    'raspberry_pi_4': {
        'recommended': 'hybrid',
        'alternatives': ['enhanced_motion', 'enhanced_edge'],
        'avoid': [],
        'reason': 'Sufficient resources for maximum accuracy'
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