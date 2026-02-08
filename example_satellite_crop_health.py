#!/usr/bin/env python3
"""
Example script demonstrating how to use the Sentinel satellite crop health testing feature.
This script shows basic usage of the satellite utilities for crop health analysis.
"""

import sys
import os
import json

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from tests.utils.satellite_utils import (
    SentinelDataProcessor,
    MockSentinelDataFetcher,
    validate_satellite_data,
    save_analysis_results
)


def main():
    """Main function demonstrating satellite crop health analysis."""
    
    print("=" * 70)
    print("Sentinel Satellite Crop Health Analysis - Example")
    print("=" * 70)
    
    # Initialize the processor and fetcher
    processor = SentinelDataProcessor()
    fetcher = MockSentinelDataFetcher()
    
    # Example farm location (coordinates in India)
    farm_location = {
        "name": "Example Farm",
        "latitude": 28.7041,  # Delhi region
        "longitude": 77.1025,
        "description": "Sample farmland for demonstration"
    }
    
    print(f"\n📍 Analyzing crop health for: {farm_location['name']}")
    print(f"   Location: ({farm_location['latitude']}, {farm_location['longitude']})")
    
    # Step 1: Fetch satellite data
    print("\n🛰️  Step 1: Fetching Sentinel satellite data...")
    satellite_data = fetcher.fetch_satellite_data(
        latitude=farm_location["latitude"],
        longitude=farm_location["longitude"],
        cloud_coverage_max=20
    )
    
    # Validate the data
    is_valid, message = validate_satellite_data(satellite_data)
    if not is_valid:
        print(f"   ❌ Error: {message}")
        return 1
    
    print(f"   ✓ Data source: {satellite_data['data_source']}")
    print(f"   ✓ Acquisition date: {satellite_data['acquisition_date']}")
    print(f"   ✓ Cloud coverage: {satellite_data['cloud_coverage']}%")
    print(f"   ✓ Scene ID: {satellite_data['scene_id']}")
    
    # Step 2: Generate band data (in production, this would come from actual satellite)
    print("\n📊 Step 2: Processing satellite band data...")
    band_data = fetcher.generate_mock_band_data(
        size=(100, 100),
        health_level="moderate"  # Options: healthy, moderate, poor, unhealthy
    )
    print(f"   ✓ Processed {band_data['red'].size} pixels")
    print(f"   ✓ Bands available: Blue, Red, NIR")
    
    # Step 3: Calculate vegetation indices
    print("\n🌱 Step 3: Calculating vegetation indices...")
    
    # Calculate NDVI
    ndvi = processor.calculate_ndvi(band_data["red"], band_data["nir"])
    print(f"   ✓ NDVI calculated")
    
    # Calculate EVI
    evi = processor.calculate_evi(band_data["red"], band_data["nir"], band_data["blue"])
    print(f"   ✓ EVI calculated")
    
    # Calculate SAVI
    savi = processor.calculate_savi(band_data["red"], band_data["nir"])
    print(f"   ✓ SAVI calculated")
    
    # Step 4: Analyze crop health
    print("\n🔍 Step 4: Analyzing crop health...")
    analysis = processor.analyze_crop_health(ndvi)
    
    if analysis["status"] != "success":
        print(f"   ❌ Analysis failed: {analysis.get('message')}")
        return 1
    
    # Display results
    print("\n" + "=" * 70)
    print("📈 CROP HEALTH ANALYSIS RESULTS")
    print("=" * 70)
    
    stats = analysis["statistics"]
    print(f"\n📊 NDVI Statistics:")
    print(f"   • Mean NDVI:   {stats['mean_ndvi']:.3f}")
    print(f"   • Median NDVI: {stats['median_ndvi']:.3f}")
    print(f"   • Std Dev:     {stats['std_ndvi']:.3f}")
    print(f"   • Min NDVI:    {stats['min_ndvi']:.3f}")
    print(f"   • Max NDVI:    {stats['max_ndvi']:.3f}")
    
    print(f"\n🏥 Health Classification: {analysis['classification']}")
    
    distribution = analysis["distribution"]
    print(f"\n📈 Health Distribution:")
    print(f"   • Healthy (NDVI ≥ 0.7):   {distribution['healthy_percent']:.1f}%")
    print(f"   • Moderate (0.5-0.7):     {distribution['moderate_percent']:.1f}%")
    print(f"   • Poor (0.2-0.5):         {distribution['poor_percent']:.1f}%")
    print(f"   • Unhealthy (< 0.2):      {distribution['unhealthy_percent']:.1f}%")
    
    print(f"\n📍 Total pixels analyzed: {analysis['total_pixels_analyzed']}")
    
    # Step 5: Save results
    print("\n💾 Step 5: Saving analysis results...")
    output_dir = "test-flows"
    output_file = os.path.join(output_dir, "example_crop_health_analysis.json")
    
    results = {
        "farm_info": farm_location,
        "satellite_data": satellite_data,
        "crop_health_analysis": analysis
    }
    
    save_analysis_results(results, output_file)
    print(f"   ✓ Results saved to: {output_file}")
    
    # Print health recommendation
    print("\n" + "=" * 70)
    print("💡 RECOMMENDATIONS")
    print("=" * 70)
    
    mean_ndvi = stats['mean_ndvi']
    healthy_pct = distribution['healthy_percent']
    
    if mean_ndvi >= 0.7:
        print("✅ Crops are in excellent health. Continue current management practices.")
    elif mean_ndvi >= 0.5:
        print("⚠️  Crops show moderate health. Consider:")
        print("   • Checking irrigation and water availability")
        print("   • Monitoring for pest or disease issues")
        print("   • Verifying nutrient levels")
    elif mean_ndvi >= 0.2:
        print("⚠️  Crops show poor health. Immediate attention needed:")
        print("   • Investigate water stress or irrigation issues")
        print("   • Check for pest infestation or diseases")
        print("   • Assess soil health and nutrient deficiencies")
        print("   • Consider consulting an agronomist")
    else:
        print("🚨 Crops are unhealthy or minimal vegetation detected:")
        print("   • Urgent intervention required")
        print("   • Investigate all possible stress factors")
        print("   • Consider replanting if necessary")
    
    print("\n" + "=" * 70)
    print("✨ Analysis complete!")
    print("=" * 70)
    
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\n⚠️  Analysis interrupted by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
