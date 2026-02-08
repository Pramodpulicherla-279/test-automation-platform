"""
Utilities for fetching and processing Sentinel satellite data for crop health analysis.
This module provides functions to:
- Fetch Sentinel-2 satellite imagery
- Calculate vegetation indices (NDVI, EVI, etc.)
- Analyze crop health metrics
"""

import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import numpy as np


class SentinelDataProcessor:
    """
    Processor for Sentinel satellite data to analyze crop health.
    Supports NDVI (Normalized Difference Vegetation Index) and other metrics.
    """
    
    def __init__(self):
        """Initialize the Sentinel data processor."""
        self.supported_indices = ["NDVI", "EVI", "SAVI"]
    
    def calculate_ndvi(self, red_band: np.ndarray, nir_band: np.ndarray) -> np.ndarray:
        """
        Calculate Normalized Difference Vegetation Index (NDVI).
        
        NDVI = (NIR - Red) / (NIR + Red)
        
        Args:
            red_band: Red band reflectance values (Band 4 for Sentinel-2)
            nir_band: Near-infrared band reflectance values (Band 8 for Sentinel-2)
        
        Returns:
            NDVI values ranging from -1 to 1
        """
        # Avoid division by zero
        denominator = nir_band + red_band
        ndvi = np.where(
            denominator != 0,
            (nir_band - red_band) / denominator,
            0
        )
        return ndvi
    
    def calculate_evi(self, red_band: np.ndarray, nir_band: np.ndarray, 
                     blue_band: np.ndarray, G: float = 2.5, C1: float = 6.0, 
                     C2: float = 7.5, L: float = 1.0) -> np.ndarray:
        """
        Calculate Enhanced Vegetation Index (EVI).
        
        EVI = G * ((NIR - Red) / (NIR + C1 * Red - C2 * Blue + L))
        
        Args:
            red_band: Red band reflectance values
            nir_band: Near-infrared band reflectance values
            blue_band: Blue band reflectance values
            G: Gain factor (default 2.5)
            C1: Aerosol resistance coefficient (default 6.0)
            C2: Aerosol resistance coefficient (default 7.5)
            L: Canopy background adjustment (default 1.0)
        
        Returns:
            EVI values
        """
        denominator = nir_band + C1 * red_band - C2 * blue_band + L
        evi = np.where(
            denominator != 0,
            G * ((nir_band - red_band) / denominator),
            0
        )
        return evi
    
    def calculate_savi(self, red_band: np.ndarray, nir_band: np.ndarray, 
                      L: float = 0.5) -> np.ndarray:
        """
        Calculate Soil Adjusted Vegetation Index (SAVI).
        
        SAVI = ((NIR - Red) / (NIR + Red + L)) * (1 + L)
        
        Args:
            red_band: Red band reflectance values
            nir_band: Near-infrared band reflectance values
            L: Soil brightness correction factor (default 0.5)
        
        Returns:
            SAVI values
        """
        denominator = nir_band + red_band + L
        savi = np.where(
            denominator != 0,
            ((nir_band - red_band) / denominator) * (1 + L),
            0
        )
        return savi
    
    def classify_crop_health(self, ndvi_value: float) -> str:
        """
        Classify crop health based on NDVI value.
        
        Args:
            ndvi_value: NDVI value between -1 and 1
        
        Returns:
            Health classification string
        """
        if ndvi_value < 0:
            return "No Vegetation / Water"
        elif ndvi_value < 0.2:
            return "Bare Soil / Unhealthy"
        elif ndvi_value < 0.5:
            return "Sparse Vegetation / Poor Health"
        elif ndvi_value < 0.7:
            return "Moderate Vegetation / Fair Health"
        elif ndvi_value <= 1.0:
            return "Dense Vegetation / Healthy"
        else:
            return "Invalid NDVI"
    
    def analyze_crop_health(self, ndvi_data: np.ndarray) -> Dict:
        """
        Analyze overall crop health from NDVI data.
        
        Args:
            ndvi_data: Array of NDVI values
        
        Returns:
            Dictionary containing health statistics
        """
        # Filter out invalid values
        valid_ndvi = ndvi_data[(ndvi_data >= -1) & (ndvi_data <= 1)]
        
        if len(valid_ndvi) == 0:
            return {
                "status": "error",
                "message": "No valid NDVI data found"
            }
        
        mean_ndvi = float(np.mean(valid_ndvi))
        median_ndvi = float(np.median(valid_ndvi))
        std_ndvi = float(np.std(valid_ndvi))
        min_ndvi = float(np.min(valid_ndvi))
        max_ndvi = float(np.max(valid_ndvi))
        
        # Calculate health distribution
        healthy_pixels = np.sum(valid_ndvi >= 0.7)
        moderate_pixels = np.sum((valid_ndvi >= 0.5) & (valid_ndvi < 0.7))
        poor_pixels = np.sum((valid_ndvi >= 0.2) & (valid_ndvi < 0.5))
        unhealthy_pixels = np.sum(valid_ndvi < 0.2)
        
        total_pixels = len(valid_ndvi)
        
        return {
            "status": "success",
            "statistics": {
                "mean_ndvi": mean_ndvi,
                "median_ndvi": median_ndvi,
                "std_ndvi": std_ndvi,
                "min_ndvi": min_ndvi,
                "max_ndvi": max_ndvi
            },
            "classification": self.classify_crop_health(mean_ndvi),
            "distribution": {
                "healthy_percent": (healthy_pixels / total_pixels) * 100,
                "moderate_percent": (moderate_pixels / total_pixels) * 100,
                "poor_percent": (poor_pixels / total_pixels) * 100,
                "unhealthy_percent": (unhealthy_pixels / total_pixels) * 100
            },
            "total_pixels_analyzed": total_pixels
        }


class MockSentinelDataFetcher:
    """
    Mock data fetcher for Sentinel satellite imagery.
    In a production environment, this would connect to actual Sentinel APIs.
    For testing/automation purposes, this generates synthetic data.
    """
    
    def __init__(self):
        """Initialize the mock data fetcher."""
        self.base_url = "https://scihub.copernicus.eu/dhus"  # Actual Sentinel API endpoint
    
    def fetch_satellite_data(self, latitude: float, longitude: float, 
                            start_date: Optional[str] = None,
                            end_date: Optional[str] = None,
                            cloud_coverage_max: int = 20) -> Dict:
        """
        Fetch (or simulate) Sentinel-2 satellite data for a given location.
        
        Args:
            latitude: Latitude of the field center
            longitude: Longitude of the field center
            start_date: Start date in format YYYY-MM-DD (defaults to 30 days ago)
            end_date: End date in format YYYY-MM-DD (defaults to today)
            cloud_coverage_max: Maximum cloud coverage percentage
        
        Returns:
            Dictionary containing satellite data info and simulated band data
        """
        # Set default dates if not provided
        if end_date is None:
            end_date = datetime.now().strftime("%Y-%m-%d")
        if start_date is None:
            start_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
        
        # For automation testing, generate synthetic but realistic data
        # In production, this would make actual API calls to Copernicus Hub
        
        return {
            "status": "success",
            "query_parameters": {
                "latitude": latitude,
                "longitude": longitude,
                "start_date": start_date,
                "end_date": end_date,
                "cloud_coverage_max": cloud_coverage_max
            },
            "data_source": "Sentinel-2",
            "acquisition_date": end_date,
            "cloud_coverage": np.random.randint(0, cloud_coverage_max),
            "scene_id": f"S2A_MSIL2A_{datetime.now().strftime('%Y%m%d')}",
            "message": "Mock data for testing purposes. In production, connect to actual Sentinel API."
        }
    
    def generate_mock_band_data(self, size: Tuple[int, int] = (100, 100), 
                                health_level: str = "healthy") -> Dict[str, np.ndarray]:
        """
        Generate mock satellite band data for testing.
        
        Args:
            size: Tuple of (height, width) for the data array
            health_level: One of 'healthy', 'moderate', 'poor', 'unhealthy'
        
        Returns:
            Dictionary with mock band data (Blue, Red, NIR)
        """
        # Generate realistic band values based on health level
        if health_level == "healthy":
            red_mean, nir_mean = 0.04, 0.35  # Healthy vegetation
        elif health_level == "moderate":
            red_mean, nir_mean = 0.06, 0.25  # Moderate vegetation
        elif health_level == "poor":
            red_mean, nir_mean = 0.08, 0.18  # Poor vegetation
        else:  # unhealthy
            red_mean, nir_mean = 0.10, 0.12  # Unhealthy/bare soil
        
        # Add some noise to make it realistic
        blue_band = np.random.normal(0.03, 0.01, size).clip(0, 1)
        red_band = np.random.normal(red_mean, 0.02, size).clip(0, 1)
        nir_band = np.random.normal(nir_mean, 0.03, size).clip(0, 1)
        
        return {
            "blue": blue_band,
            "red": red_band,
            "nir": nir_band
        }


def validate_satellite_data(data: Dict) -> Tuple[bool, str]:
    """
    Validate satellite data response.
    
    Args:
        data: Satellite data dictionary
    
    Returns:
        Tuple of (is_valid, message)
    """
    if not isinstance(data, dict):
        return False, "Data is not a dictionary"
    
    if data.get("status") != "success":
        return False, f"Data fetch failed: {data.get('message', 'Unknown error')}"
    
    required_fields = ["query_parameters", "data_source", "acquisition_date"]
    for field in required_fields:
        if field not in data:
            return False, f"Missing required field: {field}"
    
    return True, "Data is valid"


def save_analysis_results(results: Dict, output_path: str) -> None:
    """
    Save crop health analysis results to a JSON file.
    
    Args:
        results: Analysis results dictionary
        output_path: Path to save the results
    """
    dir_path = os.path.dirname(output_path)
    if dir_path:  # Only create directory if path has a directory component
        os.makedirs(dir_path, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=4)
