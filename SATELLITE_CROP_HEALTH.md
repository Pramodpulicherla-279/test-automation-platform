# Sentinel Satellite Crop Health Testing

## Overview

This feature enables automated testing of crop health using Sentinel satellite imagery data. The platform can analyze vegetation indices (NDVI, EVI, SAVI) to assess crop health conditions and generate automated test reports.

## Features

### 1. Vegetation Index Calculations
- **NDVI (Normalized Difference Vegetation Index)**: Measures vegetation health and density
- **EVI (Enhanced Vegetation Index)**: Improved sensitivity in high biomass regions
- **SAVI (Soil Adjusted Vegetation Index)**: Minimizes soil brightness influences

### 2. Crop Health Classification
The system classifies crop health into categories based on NDVI values:
- **Dense Vegetation / Healthy** (NDVI: 0.7 - 1.0)
- **Moderate Vegetation / Fair Health** (NDVI: 0.5 - 0.7)
- **Sparse Vegetation / Poor Health** (NDVI: 0.2 - 0.5)
- **Bare Soil / Unhealthy** (NDVI: < 0.2)

### 3. Automated Testing
- Automated test cases for validating crop health calculations
- Parameterized tests for different vegetation health levels
- Integration tests for end-to-end workflows
- Results export to JSON for further analysis

## API Endpoints

### Fetch Satellite Data
```
POST /api/satellite/fetch-data
```

**Request Body:**
```json
{
  "latitude": 28.7041,
  "longitude": 77.1025,
  "start_date": "2024-01-01",
  "end_date": "2024-01-31",
  "cloud_coverage_max": 20
}
```

**Response:**
```json
{
  "status": "success",
  "query_parameters": {
    "latitude": 28.7041,
    "longitude": 77.1025,
    "start_date": "2024-01-01",
    "end_date": "2024-01-31"
  },
  "data_source": "Sentinel-2",
  "acquisition_date": "2024-01-31",
  "cloud_coverage": 15,
  "scene_id": "S2A_MSIL2A_20240131"
}
```

### Analyze Crop Health
```
POST /api/satellite/analyze-crop-health
```

**Request Body:**
```json
{
  "latitude": 28.7041,
  "longitude": 77.1025,
  "health_level": "moderate",
  "size": 100
}
```

**Response:**
```json
{
  "satellite_info": {
    "acquisition_date": "2024-01-31",
    "cloud_coverage": 10,
    "scene_id": "S2A_MSIL2A_20240131",
    "location": {
      "latitude": 28.7041,
      "longitude": 77.1025
    }
  },
  "crop_health_analysis": {
    "status": "success",
    "statistics": {
      "mean_ndvi": 0.65,
      "median_ndvi": 0.64,
      "std_ndvi": 0.08,
      "min_ndvi": 0.45,
      "max_ndvi": 0.85
    },
    "classification": "Moderate Vegetation / Fair Health",
    "distribution": {
      "healthy_percent": 25.5,
      "moderate_percent": 55.2,
      "poor_percent": 15.3,
      "unhealthy_percent": 4.0
    },
    "total_pixels_analyzed": 10000
  }
}
```

### Run Automated Tests
```
POST /api/satellite/run-tests
```

**Response:**
```json
{
  "status": "started",
  "message": "Satellite crop health tests started in background"
}
```

## Usage Examples

### Python Script Example

```python
from tests.utils.satellite_utils import (
    SentinelDataProcessor,
    MockSentinelDataFetcher
)

# Initialize
processor = SentinelDataProcessor()
fetcher = MockSentinelDataFetcher()

# Fetch satellite data
satellite_data = fetcher.fetch_satellite_data(
    latitude=28.7041,
    longitude=77.1025,
    cloud_coverage_max=20
)

# Generate band data (in production, this would be from actual satellite)
band_data = fetcher.generate_mock_band_data(
    size=(100, 100),
    health_level="moderate"
)

# Calculate NDVI
ndvi = processor.calculate_ndvi(band_data["red"], band_data["nir"])

# Analyze crop health
analysis = processor.analyze_crop_health(ndvi)

print(f"Mean NDVI: {analysis['statistics']['mean_ndvi']}")
print(f"Classification: {analysis['classification']}")
print(f"Healthy Coverage: {analysis['distribution']['healthy_percent']}%")
```

### Running Tests

Run the complete test suite:
```bash
pytest tests/test_cases/test_crop_health_satellite.py -v
```

Run specific test:
```bash
pytest tests/test_cases/test_crop_health_satellite.py::TestCropHealthSatellite::test_ndvi_calculation_healthy -v
```

Run with Allure reporting:
```bash
pytest tests/test_cases/test_crop_health_satellite.py --alluredir=allure-results
allure serve allure-results
```

## Integration with Existing Platform

The satellite crop health testing is integrated into the existing test automation platform:

1. **Backend Integration**: New API endpoints are added to `backend/server.py`
2. **Test Runner**: Tests can be executed through the existing test runner infrastructure
3. **Reporting**: Results are integrated with Allure reporting
4. **WebSocket Support**: Real-time test status updates via WebSocket

## Test Coverage

The test suite includes:
- ✅ NDVI calculation for healthy vegetation
- ✅ NDVI calculation for unhealthy vegetation
- ✅ EVI calculation tests
- ✅ SAVI calculation tests
- ✅ Satellite data fetching validation
- ✅ Complete crop health analysis workflow
- ✅ Parameterized tests for different health levels
- ✅ End-to-end integration tests
- ✅ Results export functionality

## Technical Details

### Dependencies
- `numpy`: For numerical computations
- `pytest`: Test framework
- `allure-pytest`: Test reporting
- `pydantic`: Data validation (FastAPI)
- `fastapi`: Web framework for API endpoints

### Data Sources
- **Mock Data**: For testing and development, synthetic data is generated
- **Production**: Can be extended to connect to actual Sentinel Hub API (Copernicus)

### Sentinel-2 Bands Used
- **Band 2 (Blue)**: 490 nm wavelength
- **Band 4 (Red)**: 665 nm wavelength
- **Band 8 (NIR)**: 842 nm wavelength

## Future Enhancements

Potential improvements for production use:
1. Connect to actual Sentinel Hub API (requires credentials)
2. Add support for Sentinel-1 SAR data
3. Implement time-series analysis for crop growth tracking
4. Add crop type classification using machine learning
5. Generate PDF reports with maps and visualizations
6. Add alert system for crop stress detection
7. Integrate with mobile app for field-level monitoring

## Troubleshooting

### Common Issues

**Issue**: Tests fail with import errors
```bash
# Solution: Ensure you're running from project root
cd /path/to/test-automation-platform
pytest tests/test_cases/test_crop_health_satellite.py
```

**Issue**: NumPy not installed
```bash
# Solution: Install required dependencies
pip install numpy pytest allure-pytest
```

**Issue**: API endpoints return 500 errors
```bash
# Solution: Check that satellite_utils.py is properly imported
# Verify Python path includes the tests directory
```

## License

This feature is part of the test-automation-platform and follows the same license terms.

## Support

For questions or issues related to satellite crop health testing, please create an issue in the repository.
