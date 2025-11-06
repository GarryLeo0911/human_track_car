#!/usr/bin/env python3
"""
Lightweight Detector Selection Assistant
Help users choose the most suitable detector based on hardware and requirements
"""

import sys
import os

# 添加项目路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config.lightweight_detector_config import (
    DETECTOR_CONFIGS,
    PLATFORM_RECOMMENDATIONS,
    SCENARIO_RECOMMENDATIONS,
    PERFORMANCE_TARGETS,
    recommend_detector,
    print_detector_info
)

def interactive_selector():
    """Interactive detector selector"""
    print("🎯 Lightweight Human Detector Selection Assistant")
    print("=" * 50)
    
    # 1. Hardware platform selection
    print("\n📱 Please select your hardware platform:")
    platforms = {
        '1': 'raspberry_pi_zero',
        '2': 'raspberry_pi_3', 
        '3': 'raspberry_pi_4',
        '4': 'other'
    }
    
    for key, platform in platforms.items():
        print(f"  {key}. {platform.replace('_', ' ').title()}")
    
    platform_choice = input("\nEnter choice (1-4): ").strip()
    selected_platform = platforms.get(platform_choice, 'other')
    
    # 2. Application scenario selection
    print("\n🎬 Please select your application scenario:")
    scenarios = {
        '1': 'indoor_tracking',
        '2': 'outdoor_tracking',
        '3': 'real_time_following',
        '4': 'security_monitoring',
        '5': 'demo_showcase'
    }
    
    for key, scenario in scenarios.items():
        print(f"  {key}. {scenario.replace('_', ' ').title()}")
    
    scenario_choice = input("\nEnter choice (1-5): ").strip()
    selected_scenario = scenarios.get(scenario_choice)
    
    # 3. Performance target selection
    print("\n⚡ Please select your performance target:")
    targets = {
        '1': 'ultra_low_power',
        '2': 'balanced',
        '3': 'high_accuracy'
    }
    
    for key, target in targets.items():
        target_info = PERFORMANCE_TARGETS[target]
        print(f"  {key}. {target.replace('_', ' ').title()} (CPU<{target_info['max_cpu_usage']}%, Memory<{target_info['max_memory']}MB)")
    
    target_choice = input("\nEnter choice (1-3): ").strip()
    selected_target = targets.get(target_choice, 'balanced')
    
    # 4. Generate recommendation
    print("\n🔍 Analyzing...")
    recommended, details = recommend_detector(
        platform=selected_platform,
        scenario=selected_scenario, 
        performance_target=selected_target
    )
    
    # 5. Display results
    print(f"\n✅ Recommended Detector: {recommended.upper()}")
    print(f"Recommendation Basis: {details}")
    
    # Display detailed information
    print_detector_info(recommended)
    
    # 6. Generate startup command
    print(f"\n🚀 Startup Command:")
    print(f"python main.py --detector {recommended} --platform {selected_platform}")
    
    # 7. Show alternatives
    platform_rec = PLATFORM_RECOMMENDATIONS.get(selected_platform, {})
    alternatives = platform_rec.get('alternatives', [])
    
    if alternatives:
        print(f"\n🔄 Alternative Options:")
        for alt in alternatives:
            print(f"  python main.py --detector {alt} --platform {selected_platform}")

def quick_recommendation():
    """Quick recommendation"""
    print("⚡ Quick Recommendation Guide")
    print("=" * 30)
    
    recommendations = {
        "Raspberry Pi performance insufficient": "motion",
        "Need to detect stationary humans": "edge",
        "Indoor fixed lighting": "color", 
        "Long-term monitoring operation": "background",
        "Unsure of choice": "auto"
    }
    
    for situation, detector in recommendations.items():
        config = DETECTOR_CONFIGS[detector]
        print(f"\n{situation}: {detector} ({config['name']})")
        print(f"  Command: python main.py --detector {detector}")
        print(f"  Performance: {config['detection_time']}, {config['cpu_usage']}")

def performance_comparison():
    """Performance comparison"""
    print("📊 Detector Performance Comparison")
    print("=" * 60)
    
    print(f"{'Detector':<12} {'Det.Time':<10} {'CPU Usage':<10} {'Memory':<10} {'Description':<20}")
    print("-" * 60)
    
    # Sort by performance
    sorted_detectors = [
        ('motion', DETECTOR_CONFIGS['motion']),
        ('color', DETECTOR_CONFIGS['color']),
        ('edge', DETECTOR_CONFIGS['edge']),
        ('background', DETECTOR_CONFIGS['background'])
    ]
    
    for detector_type, config in sorted_detectors:
        print(f"{detector_type:<12} {config['detection_time']:<10} {config['cpu_usage']:<10} "
              f"{config['memory_usage']:<10} {config['name']:<20}")
    
    print(f"\n💡 Performance Notes:")
    print(f"  🟢 Green Recommendation: motion (most lightweight)")
    print(f"  🟡 Yellow Recommendation: edge (balanced)")
    print(f"  🟠 Orange Recommendation: background (high accuracy)")

def main():
    """Main function"""
    if len(sys.argv) > 1:
        mode = sys.argv[1]
        if mode == 'quick':
            quick_recommendation()
        elif mode == 'compare':
            performance_comparison()
        elif mode == 'info':
            if len(sys.argv) > 2:
                detector_type = sys.argv[2]
                if detector_type in DETECTOR_CONFIGS:
                    print_detector_info(detector_type)
                else:
                    print(f"Unknown detector: {detector_type}")
                    print(f"Available detectors: {list(DETECTOR_CONFIGS.keys())}")
            else:
                print("Usage: python detector_selector.py info <detector_type>")
        else:
            print("Usage:")
            print("  python detector_selector.py          # Interactive selection")
            print("  python detector_selector.py quick    # Quick recommendations")
            print("  python detector_selector.py compare  # Performance comparison")
            print("  python detector_selector.py info <detector>  # Detailed information")
    else:
        interactive_selector()

if __name__ == "__main__":
    main()