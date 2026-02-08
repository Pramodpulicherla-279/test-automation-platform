# Test Automation Platform

A comprehensive test automation platform for mobile applications with integrated Sentinel satellite crop health monitoring.

## Features

### Mobile App Testing
- Automated testing for Android mobile applications
- Appium-based test execution
- Allure reporting for test results
- Real-time test status via WebSocket

### Satellite Crop Health Monitoring
- **NEW**: Sentinel satellite data integration for crop health analysis
- NDVI, EVI, and SAVI vegetation index calculations
- Automated crop health classification
- REST API endpoints for satellite data analysis
- Comprehensive test suite for satellite functionality

## Quick Start

### Run Satellite Crop Health Example
```bash
python example_satellite_crop_health.py
```

### Run Satellite Tests
```bash
pytest tests/test_cases/test_crop_health_satellite.py -v --noconftest
```

### Start Backend Server
```bash
cd backend
python server.py
```

## Documentation

- [Satellite Crop Health Testing Guide](SATELLITE_CROP_HEALTH.md) - Complete documentation for satellite features

## API Endpoints

### Satellite Crop Health
- `POST /api/satellite/fetch-data` - Fetch Sentinel satellite data
- `POST /api/satellite/analyze-crop-health` - Analyze crop health
- `POST /api/satellite/run-tests` - Run automated satellite tests

## License

See repository license for details.