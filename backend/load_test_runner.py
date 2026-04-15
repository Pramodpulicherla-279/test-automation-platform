"""
Load testing runner - Executes k6 load tests and collects performance metrics
"""

import json
import subprocess
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any
import re
import asyncio
from dataclasses import dataclass, asdict
import tempfile


@dataclass
class MetricPoint:
    """Single data point for a metric"""
    timestamp: float
    value: float
    endpoint: str = ""
    status: int = 0


@dataclass
class PerformanceMetrics:
    """Aggregated performance metrics"""
    endpoint: str
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    avg_response_time: float = 0
    min_response_time: float = 0
    max_response_time: float = 0
    p95_response_time: float = 0
    p99_response_time: float = 0
    throughput: float = 0  # requests per second
    error_rate: float = 0  # percentage
    status_codes: Dict[int, int] = None  # status_code: count
    
    def __post_init__(self):
        if self.status_codes is None:
            self.status_codes = {}


class K6LoadTestRunner:
    """Executes k6 load tests and collects metrics"""
    
    def __init__(self, k6_script_path: str = None):
        self.k6_script_path = k6_script_path
        self.test_results_dir = Path("backend/api_matrix_data/load_test_results")
        self.test_results_dir.mkdir(parents=True, exist_ok=True)
        self.current_test_id = None
        self.metrics_data: Dict[str, List[MetricPoint]] = {}
        
    def create_k6_script(self, test_config: Dict) -> str:
        """
        Create a k6 script from test configuration
        Returns the path to the created script
        """
        script_content = f"""
import {{ sleep, check }} from 'k6';
import http from 'k6/http';

export const options = {json.dumps(test_config.get('options', {}), indent=2)};

const bearerToken = '{test_config.get('bearer_token', '')}';
const commonHeaders = {json.dumps(test_config.get('headers', {}), indent=2)};

export function scenario_1() {{
    const requests = {json.dumps(test_config.get('requests', []), indent=2)};
    let responses = http.batch(requests);
    
    // Tag responses with their endpoint names
    responses.forEach((res, idx) => {{
        if (requests[idx].params && requests[idx].params.tags) {{
            console.log(`${{requests[idx].params.tags.name}}: ${{res.status}} - ${{res.timings.duration}}ms`);
        }}
    }});
    
    sleep(1);
}}
"""
        # Create temp file
        temp_dir = Path(tempfile.gettempdir()) / "k6_tests"
        temp_dir.mkdir(exist_ok=True)
        script_file = temp_dir / f"test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.js"
        
        with open(script_file, 'w') as f:
            f.write(script_content)
        
        return str(script_file)
    
    async def run_test(self, test_config: Dict, test_id: str = None) -> Dict:
        """
        Run k6 load test with the provided configuration
        Streams metrics back to caller
        """
        if test_id is None:
            test_id = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        self.current_test_id = test_id
        self.metrics_data = {}
        
        # Create k6 script
        script_path = self.create_k6_script(test_config)
        
        # Prepare k6 command
        k6_cmd = [
            "k6",
            "run",
            "--out", "json=" + str(self.test_results_dir / f"{test_id}_metrics.json"),
            script_path
        ]
        
        try:
            # Run k6 with line-by-line output capture
            process = await asyncio.create_subprocess_exec(
                *k6_cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                text=True
            )
            
            # Read output line by line
            metrics = []
            async for line in process.stdout:
                line = line.strip()
                if line:
                    # Parse k6 output for metrics
                    metrics.append(line)
                    # Extract endpoint metrics
                    self._parse_k6_output(line)
            
            # Wait for process to complete
            return_code = await process.wait()
            
            # Parse final results
            results_file = self.test_results_dir / f"{test_id}_metrics.json"
            if results_file.exists():
                with open(results_file, 'r') as f:
                    results = json.load(f)
                
                return {
                    "success": return_code == 0,
                    "test_id": test_id,
                    "metrics": self._aggregate_metrics(results),
                    "raw_output": metrics,
                    "results_file": str(results_file)
                }
            
            return {
                "success": False,
                "test_id": test_id,
                "error": "No results file generated",
                "metrics": {}
            }
            
        except Exception as e:
            return {
                "success": False,
                "test_id": test_id,
                "error": str(e),
                "metrics": {}
            }
    
    def _parse_k6_output(self, line: str):
        """Parse k6 output lines for metric extraction"""
        # This extracts endpoint metrics from console.log statements
        # Format: "endpoint_name: status - duration_ms"
        pattern = r'(\w+(?:-\w+)*): (\d+) - (\d+)ms'
        match = re.search(pattern, line)
        
        if match:
            endpoint = match.group(1)
            status = int(match.group(2))
            duration = int(match.group(3))
            
            if endpoint not in self.metrics_data:
                self.metrics_data[endpoint] = []
            
            self.metrics_data[endpoint].append(
                MetricPoint(
                    timestamp=datetime.now().timestamp(),
                    value=duration,
                    endpoint=endpoint,
                    status=status
                )
            )
    
    def _aggregate_metrics(self, k6_results: Dict) -> Dict[str, PerformanceMetrics]:
        """Aggregate k6 results into performance metrics"""
        aggregated = {}
        
        # Parse k6 JSON output
        for metric in k6_results.get('metrics', []):
            if metric.get('type') == 'http_reqs':
                # Count requests per endpoint
                endpoint = self._extract_endpoint_name(metric)
                if endpoint not in aggregated:
                    aggregated[endpoint] = PerformanceMetrics(endpoint=endpoint)
        
        # Convert to dict for JSON serialization
        return {
            endpoint: asdict(metrics)
            for endpoint, metrics in aggregated.items()
        }
    
    def _extract_endpoint_name(self, metric: Dict) -> str:
        """Extract endpoint name from k6 metric"""
        tags = metric.get('tags', {})
        return tags.get('name', 'unknown')
    
    def get_test_results(self, test_id: str) -> Optional[Dict]:
        """Retrieve stored test results"""
        results_file = self.test_results_dir / f"{test_id}_metrics.json"
        
        if results_file.exists():
            with open(results_file, 'r') as f:
                return json.load(f)
        
        return None
    
    def list_tests(self) -> List[Dict]:
        """List all completed test runs"""
        tests = []
        
        for file in self.test_results_dir.glob("*_metrics.json"):
            test_id = file.stem.replace("_metrics", "")
            tests.append({
                "test_id": test_id,
                "file": str(file),
                "created": datetime.fromtimestamp(file.stat().st_mtime).isoformat()
            })
        
        return sorted(tests, key=lambda x: x['created'], reverse=True)
