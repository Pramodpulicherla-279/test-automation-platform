"""
Test cases for Sentinel satellite crop health monitoring and analysis.
This module tests the automated crop health assessment using satellite data.
"""

import pytest
import allure
import json
import os
from datetime import datetime
import numpy as np
import sys

# Add parent directory to path to import utilities
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from utils.satellite_utils import (
    SentinelDataProcessor,
    MockSentinelDataFetcher,
    validate_satellite_data,
    save_analysis_results
)


@allure.epic("Satellite Monitoring")
@allure.feature("Crop Health Analysis")
class TestCropHealthSatellite:
    """Test suite for automated crop health monitoring using Sentinel satellite data."""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test fixtures."""
        self.processor = SentinelDataProcessor()
        self.fetcher = MockSentinelDataFetcher()
        self.test_results = []
    
    @allure.story("NDVI Calculation")
    @allure.title("Test NDVI calculation with healthy vegetation")
    def test_ndvi_calculation_healthy(self):
        """Test NDVI calculation for healthy crop conditions."""
        with allure.step("Generate mock healthy vegetation band data"):
            # Healthy vegetation: high NIR, low Red
            red_band = np.array([[0.04, 0.05], [0.05, 0.04]])
            nir_band = np.array([[0.35, 0.36], [0.34, 0.37]])
            
            allure.attach(
                f"Red band values: {red_band.tolist()}\nNIR band values: {nir_band.tolist()}",
                name="Input Band Data",
                attachment_type=allure.attachment_type.TEXT
            )
        
        with allure.step("Calculate NDVI"):
            ndvi = self.processor.calculate_ndvi(red_band, nir_band)
            mean_ndvi = float(np.mean(ndvi))
            
            allure.attach(
                f"NDVI values: {ndvi.tolist()}\nMean NDVI: {mean_ndvi}",
                name="NDVI Results",
                attachment_type=allure.attachment_type.TEXT
            )
        
        with allure.step("Verify NDVI values are in healthy range"):
            assert np.all(ndvi >= 0.7), f"Expected healthy NDVI (>= 0.7), got mean {mean_ndvi}"
            assert np.all(ndvi <= 1.0), "NDVI values should not exceed 1.0"
            
            classification = self.processor.classify_crop_health(mean_ndvi)
            assert classification == "Dense Vegetation / Healthy", \
                f"Expected 'Dense Vegetation / Healthy', got '{classification}'"
            
            self.test_results.append({
                "test": "NDVI Healthy",
                "status": "Passed",
                "mean_ndvi": mean_ndvi,
                "classification": classification
            })
    
    @allure.story("NDVI Calculation")
    @allure.title("Test NDVI calculation with unhealthy vegetation")
    def test_ndvi_calculation_unhealthy(self):
        """Test NDVI calculation for unhealthy crop conditions."""
        with allure.step("Generate mock unhealthy vegetation band data"):
            # Unhealthy vegetation: low NIR, high Red (similar reflectance)
            red_band = np.array([[0.10, 0.11], [0.09, 0.10]])
            nir_band = np.array([[0.12, 0.13], [0.11, 0.14]])
            
            allure.attach(
                f"Red band values: {red_band.tolist()}\nNIR band values: {nir_band.tolist()}",
                name="Input Band Data",
                attachment_type=allure.attachment_type.TEXT
            )
        
        with allure.step("Calculate NDVI"):
            ndvi = self.processor.calculate_ndvi(red_band, nir_band)
            mean_ndvi = float(np.mean(ndvi))
            
            allure.attach(
                f"NDVI values: {ndvi.tolist()}\nMean NDVI: {mean_ndvi}",
                name="NDVI Results",
                attachment_type=allure.attachment_type.TEXT
            )
        
        with allure.step("Verify NDVI values are in unhealthy range"):
            assert np.all(ndvi < 0.5), f"Expected unhealthy NDVI (< 0.5), got mean {mean_ndvi}"
            assert np.all(ndvi >= -1.0), "NDVI values should not be less than -1.0"
            
            classification = self.processor.classify_crop_health(mean_ndvi)
            assert "Unhealthy" in classification or "Poor" in classification or "Sparse" in classification, \
                f"Expected unhealthy classification, got '{classification}'"
            
            self.test_results.append({
                "test": "NDVI Unhealthy",
                "status": "Passed",
                "mean_ndvi": mean_ndvi,
                "classification": classification
            })
    
    @allure.story("EVI Calculation")
    @allure.title("Test EVI calculation for vegetation monitoring")
    def test_evi_calculation(self):
        """Test Enhanced Vegetation Index calculation."""
        with allure.step("Generate mock band data for EVI"):
            blue_band = np.array([[0.03, 0.03], [0.03, 0.03]])
            red_band = np.array([[0.05, 0.05], [0.05, 0.05]])
            nir_band = np.array([[0.35, 0.35], [0.35, 0.35]])
        
        with allure.step("Calculate EVI"):
            evi = self.processor.calculate_evi(red_band, nir_band, blue_band)
            mean_evi = float(np.mean(evi))
            
            allure.attach(
                f"EVI values: {evi.tolist()}\nMean EVI: {mean_evi}",
                name="EVI Results",
                attachment_type=allure.attachment_type.TEXT
            )
        
        with allure.step("Verify EVI calculation"):
            assert np.all(np.isfinite(evi)), "EVI values should be finite"
            assert mean_evi > 0, f"Expected positive EVI for vegetation, got {mean_evi}"
            
            self.test_results.append({
                "test": "EVI Calculation",
                "status": "Passed",
                "mean_evi": mean_evi
            })
    
    @allure.story("SAVI Calculation")
    @allure.title("Test SAVI calculation for soil-adjusted vegetation index")
    def test_savi_calculation(self):
        """Test Soil Adjusted Vegetation Index calculation."""
        with allure.step("Generate mock band data for SAVI"):
            red_band = np.array([[0.06, 0.06], [0.06, 0.06]])
            nir_band = np.array([[0.30, 0.30], [0.30, 0.30]])
        
        with allure.step("Calculate SAVI"):
            savi = self.processor.calculate_savi(red_band, nir_band)
            mean_savi = float(np.mean(savi))
            
            allure.attach(
                f"SAVI values: {savi.tolist()}\nMean SAVI: {mean_savi}",
                name="SAVI Results",
                attachment_type=allure.attachment_type.TEXT
            )
        
        with allure.step("Verify SAVI calculation"):
            assert np.all(np.isfinite(savi)), "SAVI values should be finite"
            assert mean_savi > 0, f"Expected positive SAVI for vegetation, got {mean_savi}"
            
            self.test_results.append({
                "test": "SAVI Calculation",
                "status": "Passed",
                "mean_savi": mean_savi
            })
    
    @allure.story("Data Fetching")
    @allure.title("Test satellite data fetching for a farm location")
    def test_fetch_satellite_data(self):
        """Test fetching satellite data for a specific location."""
        with allure.step("Define farm location"):
            # Example coordinates (Indian farmland)
            latitude = 28.7041  # Delhi region
            longitude = 77.1025
            
            allure.attach(
                f"Latitude: {latitude}\nLongitude: {longitude}",
                name="Farm Coordinates",
                attachment_type=allure.attachment_type.TEXT
            )
        
        with allure.step("Fetch satellite data"):
            data = self.fetcher.fetch_satellite_data(
                latitude=latitude,
                longitude=longitude,
                cloud_coverage_max=20
            )
            
            allure.attach(
                json.dumps(data, indent=2),
                name="Satellite Data Response",
                attachment_type=allure.attachment_type.JSON
            )
        
        with allure.step("Validate satellite data"):
            is_valid, message = validate_satellite_data(data)
            assert is_valid, f"Satellite data validation failed: {message}"
            assert data["status"] == "success", "Data fetch should be successful"
            assert "query_parameters" in data, "Response should contain query parameters"
            
            self.test_results.append({
                "test": "Satellite Data Fetch",
                "status": "Passed",
                "location": f"{latitude}, {longitude}",
                "cloud_coverage": data.get("cloud_coverage")
            })
    
    @allure.story("Crop Health Analysis")
    @allure.title("Test complete crop health analysis workflow")
    def test_complete_crop_health_analysis(self):
        """Test the complete workflow of crop health analysis."""
        with allure.step("Step 1: Fetch satellite data"):
            satellite_data = self.fetcher.fetch_satellite_data(
                latitude=28.7041,
                longitude=77.1025
            )
            assert satellite_data["status"] == "success", "Satellite data fetch failed"
        
        with allure.step("Step 2: Generate band data for analysis"):
            band_data = self.fetcher.generate_mock_band_data(
                size=(100, 100),
                health_level="moderate"
            )
            assert "red" in band_data and "nir" in band_data, "Band data should contain red and NIR bands"
        
        with allure.step("Step 3: Calculate NDVI"):
            ndvi = self.processor.calculate_ndvi(
                band_data["red"],
                band_data["nir"]
            )
            assert ndvi.shape == (100, 100), "NDVI should have same shape as input bands"
        
        with allure.step("Step 4: Analyze crop health"):
            analysis = self.processor.analyze_crop_health(ndvi)
            
            allure.attach(
                json.dumps(analysis, indent=2),
                name="Crop Health Analysis",
                attachment_type=allure.attachment_type.JSON
            )
            
            assert analysis["status"] == "success", "Analysis should be successful"
            assert "statistics" in analysis, "Analysis should contain statistics"
            assert "classification" in analysis, "Analysis should contain classification"
            assert "distribution" in analysis, "Analysis should contain health distribution"
        
        with allure.step("Step 5: Verify analysis results"):
            stats = analysis["statistics"]
            assert -1 <= stats["mean_ndvi"] <= 1, "Mean NDVI should be between -1 and 1"
            assert stats["std_ndvi"] >= 0, "Standard deviation should be non-negative"
            
            distribution = analysis["distribution"]
            total_percent = (
                distribution["healthy_percent"] +
                distribution["moderate_percent"] +
                distribution["poor_percent"] +
                distribution["unhealthy_percent"]
            )
            assert abs(total_percent - 100.0) < 0.1, "Distribution percentages should sum to 100%"
            
            self.test_results.append({
                "test": "Complete Analysis",
                "status": "Passed",
                "mean_ndvi": stats["mean_ndvi"],
                "classification": analysis["classification"],
                "healthy_percent": distribution["healthy_percent"]
            })
    
    @allure.story("Crop Health Analysis")
    @allure.title("Test crop health analysis with different health levels")
    @pytest.mark.parametrize("health_level,expected_range", [
        ("healthy", (0.7, 1.0)),
        ("moderate", (0.5, 0.7)),
        ("poor", (0.2, 0.5)),
        ("unhealthy", (-1.0, 0.2))
    ])
    def test_crop_health_levels(self, health_level, expected_range):
        """Test crop health analysis for different vegetation health levels."""
        with allure.step(f"Generate {health_level} vegetation data"):
            band_data = self.fetcher.generate_mock_band_data(
                size=(50, 50),
                health_level=health_level
            )
        
        with allure.step("Calculate NDVI and analyze health"):
            ndvi = self.processor.calculate_ndvi(
                band_data["red"],
                band_data["nir"]
            )
            analysis = self.processor.analyze_crop_health(ndvi)
            mean_ndvi = analysis["statistics"]["mean_ndvi"]
            
            allure.attach(
                f"Health Level: {health_level}\n"
                f"Mean NDVI: {mean_ndvi}\n"
                f"Classification: {analysis['classification']}\n"
                f"Expected Range: {expected_range}",
                name="Analysis Summary",
                attachment_type=allure.attachment_type.TEXT
            )
        
        with allure.step("Verify NDVI is in expected range"):
            min_ndvi, max_ndvi = expected_range
            assert min_ndvi <= mean_ndvi <= max_ndvi, \
                f"Expected NDVI in range {expected_range} for {health_level}, got {mean_ndvi}"
            
            self.test_results.append({
                "test": f"Health Level - {health_level}",
                "status": "Passed",
                "mean_ndvi": mean_ndvi,
                "expected_range": expected_range
            })
    
    @allure.story("Results Export")
    @allure.title("Test saving analysis results to file")
    def test_save_analysis_results(self, tmp_path):
        """Test saving crop health analysis results to a JSON file."""
        with allure.step("Perform crop health analysis"):
            band_data = self.fetcher.generate_mock_band_data(health_level="healthy")
            ndvi = self.processor.calculate_ndvi(band_data["red"], band_data["nir"])
            analysis = self.processor.analyze_crop_health(ndvi)
        
        with allure.step("Save results to file"):
            output_path = os.path.join(tmp_path, "crop_health_analysis.json")
            save_analysis_results(analysis, output_path)
            
            allure.attach(
                f"Saved to: {output_path}",
                name="Output Path",
                attachment_type=allure.attachment_type.TEXT
            )
        
        with allure.step("Verify file was created and contains valid data"):
            assert os.path.exists(output_path), "Output file should exist"
            
            with open(output_path, 'r') as f:
                loaded_data = json.load(f)
            
            assert loaded_data == analysis, "Loaded data should match original analysis"
            
            self.test_results.append({
                "test": "Save Results",
                "status": "Passed",
                "output_path": output_path
            })
    
    def teardown_method(self):
        """Save test flow results after each test method."""
        if self.test_results:
            os.makedirs("test-flows", exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"test-flows/crop_health_satellite_{timestamp}.json"
            
            with open(output_file, "w") as f:
                json.dump(self.test_results, f, indent=4)


@allure.epic("Satellite Monitoring")
@allure.feature("Integration Testing")
class TestSatelliteIntegration:
    """Integration tests for satellite-based crop monitoring."""
    
    @allure.story("End-to-End Workflow")
    @allure.title("Test end-to-end satellite crop monitoring workflow")
    def test_e2e_satellite_monitoring(self):
        """Test complete end-to-end workflow for satellite crop monitoring."""
        processor = SentinelDataProcessor()
        fetcher = MockSentinelDataFetcher()
        
        with allure.step("1. Initialize monitoring for multiple farm locations"):
            farm_locations = [
                {"name": "Farm A", "lat": 28.7041, "lon": 77.1025},
                {"name": "Farm B", "lat": 28.6139, "lon": 77.2090},
                {"name": "Farm C", "lat": 28.5355, "lon": 77.3910},
            ]
            
            allure.attach(
                json.dumps(farm_locations, indent=2),
                name="Farm Locations",
                attachment_type=allure.attachment_type.JSON
            )
        
        results = []
        
        for farm in farm_locations:
            with allure.step(f"2. Process {farm['name']}"):
                # Fetch satellite data
                sat_data = fetcher.fetch_satellite_data(
                    latitude=farm["lat"],
                    longitude=farm["lon"]
                )
                
                # Generate and analyze band data
                band_data = fetcher.generate_mock_band_data(
                    size=(100, 100),
                    health_level="moderate"
                )
                
                ndvi = processor.calculate_ndvi(band_data["red"], band_data["nir"])
                analysis = processor.analyze_crop_health(ndvi)
                
                results.append({
                    "farm_name": farm["name"],
                    "location": {"lat": farm["lat"], "lon": farm["lon"]},
                    "acquisition_date": sat_data["acquisition_date"],
                    "mean_ndvi": analysis["statistics"]["mean_ndvi"],
                    "classification": analysis["classification"],
                    "healthy_percent": analysis["distribution"]["healthy_percent"]
                })
        
        with allure.step("3. Verify all farms were analyzed"):
            assert len(results) == len(farm_locations), "All farms should be analyzed"
            
            allure.attach(
                json.dumps(results, indent=2),
                name="All Farm Analysis Results",
                attachment_type=allure.attachment_type.JSON
            )
        
        with allure.step("4. Generate summary report"):
            avg_ndvi = sum(r["mean_ndvi"] for r in results) / len(results)
            avg_healthy = sum(r["healthy_percent"] for r in results) / len(results)
            
            summary = {
                "total_farms": len(results),
                "average_ndvi": avg_ndvi,
                "average_healthy_percent": avg_healthy,
                "timestamp": datetime.now().isoformat()
            }
            
            allure.attach(
                json.dumps(summary, indent=2),
                name="Summary Report",
                attachment_type=allure.attachment_type.JSON
            )
            
            assert avg_ndvi > 0, "Average NDVI should be positive"
            assert 0 <= avg_healthy <= 100, "Healthy percentage should be 0-100%"
