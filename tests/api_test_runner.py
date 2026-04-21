"""
API Testing Integration Module
Allows running API tests alongside UI automation tests
"""

import asyncio
import aiohttp
import json
import os
from typing import List, Dict, Optional, Callable
from datetime import datetime
from pathlib import Path


class APITestRunner:
    """Runs API tests and logs results"""
    
    def __init__(self, base_url: str, log_callback: Optional[Callable] = None):
        self.base_url = base_url.rstrip('/')
        self.log_callback = log_callback
        self.results = []
    
    def log(self, message: str, status: str = "INFO"):
        """Log a message"""
        if self.log_callback:
            self.log_callback(message, status)
    
    async def run_test(self, api_config: Dict, timeout: int = 10000) -> Dict:
        """
        Run a single API test
        
        Args:
            api_config: API configuration dict with:
                - api_name: str
                - method: str (GET, POST, PUT, DELETE, PATCH)
                - endpoint: str
                - headers: Dict (optional)
                - params: Dict (optional)
                - body: Dict (optional)
                - expected_status: List[int]
            timeout: Request timeout in milliseconds
        
        Returns:
            Test result dict
        """
        try:
            url = self.base_url + api_config.get('endpoint', '')
            method = api_config.get('method', 'GET').upper()
            headers = api_config.get('headers', {})
            params = api_config.get('params', {})
            body = api_config.get('body')
            expected_status = api_config.get('expected_status', [200])
            auth_type = api_config.get('auth_type', 'none')
            auth_token = api_config.get('auth_token', '')
            
            # Add auth headers
            if auth_type == 'bearer' and auth_token:
                headers['Authorization'] = f"Bearer {auth_token}"
            elif auth_type == 'basic' and auth_token:
                headers['Authorization'] = f"Basic {auth_token}"
            
            # Ensure Content-Type
            if 'Content-Type' not in headers and body:
                headers['Content-Type'] = 'application/json'
            
            start_time = datetime.now()
            
            async with aiohttp.ClientSession() as session:
                async with session.request(
                    method=method,
                    url=url,
                    params=params or None,
                    json=body if body else None,
                    headers=headers or None,
                    timeout=aiohttp.ClientTimeout(total=timeout/1000)
                ) as resp:
                    duration = int((datetime.now() - start_time).total_seconds() * 1000)
                    status = resp.status
                    
                    try:
                        response_body = await resp.json()
                    except:
                        response_body = await resp.text()
                    
                    passed = status in expected_status
                    
                    result = {
                        'api_name': api_config.get('api_name', 'Unknown'),
                        'method': method,
                        'endpoint': api_config.get('endpoint', ''),
                        'url': url,
                        'status': status,
                        'expected_status': expected_status,
                        'passed': passed,
                        'response': response_body if isinstance(response_body, dict) else None,
                        'response_text': response_body if isinstance(response_body, str) else None,
                        'duration': duration,
                        'error': None,
                        'timestamp': start_time.isoformat()
                    }
                    
                    self.results.append(result)
                    return result
        
        except asyncio.TimeoutError:
            result = {
                'api_name': api_config.get('api_name', 'Unknown'),
                'method': api_config.get('method', 'GET'),
                'endpoint': api_config.get('endpoint', ''),
                'url': self.base_url + api_config.get('endpoint', ''),
                'status': None,
                'expected_status': api_config.get('expected_status', [200]),
                'passed': False,
                'error': 'Request timeout',
                'duration': timeout,
                'timestamp': datetime.now().isoformat()
            }
            self.results.append(result)
            return result
        
        except Exception as e:
            result = {
                'api_name': api_config.get('api_name', 'Unknown'),
                'method': api_config.get('method', 'GET'),
                'endpoint': api_config.get('endpoint', ''),
                'url': self.base_url + api_config.get('endpoint', ''),
                'status': None,
                'expected_status': api_config.get('expected_status', [200]),
                'passed': False,
                'error': str(e),
                'duration': int((datetime.now() - start_time).total_seconds() * 1000),
                'timestamp': datetime.now().isoformat()
            }
            self.results.append(result)
            return result
    
    async def run_tests(self, api_configs: List[Dict], timeout: int = 10000) -> Dict:
        """
        Run multiple API tests concurrently
        
        Args:
            api_configs: List of API configuration dicts
            timeout: Request timeout in milliseconds
        
        Returns:
            Summary dict with results and statistics
        """
        self.results = []
        self.log(f"Starting API tests: {len(api_configs)} APIs", "INFO")
        
        # Run tests
        tasks = [self.run_test(config, timeout) for config in api_configs]
        await asyncio.gather(*tasks)
        
        # Calculate statistics
        passed = len([r for r in self.results if r['passed']])
        failed = len([r for r in self.results if not r['passed']])
        total_duration = sum(r.get('duration', 0) for r in self.results)
        
        summary = {
            'total': len(self.results),
            'passed': passed,
            'failed': failed,
            'duration': total_duration,
            'timestamp': datetime.now().isoformat(),
            'results': self.results
        }
        
        self.log(f"API tests completed: {passed} passed, {failed} failed", 
                 "SUCCESS" if failed == 0 else "FAILED")
        
        return summary
    
    def run_tests_sync(self, api_configs: List[Dict], timeout: int = 10000) -> Dict:
        """
        Synchronous wrapper for running tests (for pytest integration)
        """
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(self.run_tests(api_configs, timeout))
        finally:
            loop.close()
    
    def export_results(self, output_path: str):
        """Export results to CSV"""
        if not self.results:
            self.log("No results to export", "FAILED")
            return
        
        import csv
        
        with open(output_path, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=[
                'api_name', 'method', 'endpoint', 'status', 'expected_status',
                'passed', 'duration', 'error', 'timestamp'
            ])
            writer.writeheader()
            
            for result in self.results:
                writer.writerow({
                    'api_name': result.get('api_name'),
                    'method': result.get('method'),
                    'endpoint': result.get('endpoint'),
                    'status': result.get('status', 'N/A'),
                    'expected_status': ';'.join(map(str, result.get('expected_status', []))),
                    'passed': 'YES' if result.get('passed') else 'NO',
                    'duration': result.get('duration'),
                    'error': result.get('error', ''),
                    'timestamp': result.get('timestamp')
                })
        
        self.log(f"Results exported to {output_path}", "SUCCESS")


def load_apis_from_excel(excel_path: str, sheet_name: int = 0) -> List[Dict]:
    """
    Load API configurations from Excel file
    
    Args:
        excel_path: Path to Excel file
        sheet_name: Sheet index (default 0)
    
    Returns:
        List of API configuration dicts
    """
    try:
        import pandas as pd
        
        df = pd.read_excel(excel_path, sheet_name=sheet_name)
        df.columns = df.columns.str.strip().str.lower()
        
        apis = []
        for _, row in df.iterrows():
            try:
                api_config = {
                    'api_name': str(row.get('api name', '')).strip(),
                    'method': str(row.get('method', '')).strip().upper(),
                    'endpoint': str(row.get('endpoint', '')).strip(),
                    'description': str(row.get('description', '')).strip(),
                    'headers': _parse_json(row.get('headers', '{}')),
                    'params': _parse_json(row.get('params', '{}')),
                    'body': _parse_json(row.get('body', '{}')),
                    'expected_status': _parse_status_codes(row.get('expected status', '200')),
                    'auth_type': str(row.get('auth type', 'none')).strip().lower(),
                    'auth_token': str(row.get('auth token', '')).strip(),
                }
                
                if api_config['api_name'] and api_config['method'] and api_config['endpoint']:
                    apis.append(api_config)
            except Exception as e:
                print(f"Error parsing row: {e}")
                continue
        
        return apis
    
    except Exception as e:
        raise Exception(f"Failed to load Excel: {str(e)}")


def _parse_json(value):
    """Safely parse JSON"""
    if not value or (isinstance(value, str) and value.strip() == ''):
        return {}
    
    try:
        if isinstance(value, dict):
            return value
        if isinstance(value, str):
            return json.loads(value)
        return {}
    except:
        return {}


def _parse_status_codes(value):
    """Parse status codes"""
    if not value:
        return [200]
    
    try:
        if isinstance(value, list):
            return [int(x) for x in value]
        if isinstance(value, str):
            return [int(x.strip()) for x in value.split(',') if x.strip().isdigit()]
        return [int(value)]
    except:
        return [200]
