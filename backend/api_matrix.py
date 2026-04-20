"""
API Matrix Tester Backend Module
Manages endpoints, environments, and executes API tests
"""

import json
import os
from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel
import aiohttp
import asyncio
from pathlib import Path

# ============================================================================
# DATABASE MODELS (Pydantic)
# ============================================================================

class Endpoint(BaseModel):
    id: str
    method: str
    name: str
    path: str
    auth: str = "none"
    body: str = ""
    expectedCodes: List[int] = [200]
    envIds: List[str] = []

class Environment(BaseModel):
    id: str
    name: str
    baseUrl: str
    color: str = "cyan"
    token: str = ""
    headers: Dict[str, str] = {}

class TestResult(BaseModel):
    key: str  # "{endpointId}::{envId}"
    pass_: bool
    status: Optional[int] = None
    duration: int = 0
    error: Optional[str] = None
    url: Optional[str] = None
    body: Optional[Any] = None
    timestamp: str = ""
    envName: Optional[str] = None
    epName: Optional[str] = None
    method: Optional[str] = None

class ExecutionSummary(BaseModel):
    total: int
    passed: int
    failed: int
    pending: int
    duration: int
    timestamp: str

class TestSuite(BaseModel):
    id: str
    name: str
    description: str = ""
    endpoints: List[Endpoint]
    environments: List[Environment]
    createdAt: str
    updatedAt: str

# ============================================================================
# STORAGE LAYER
# ============================================================================

class APIMatrixStorage:
    """Manages persistent storage of endpoints, environments, and results"""
    
    def __init__(self, base_dir: str = "api_matrix_data"):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(exist_ok=True)
        
        # Create subdirectories
        self.endpoints_file = self.base_dir / "endpoints.json"
        self.environments_file = self.base_dir / "environments.json"
        self.results_dir = self.base_dir / "results"
        self.suites_dir = self.base_dir / "suites"
        
        self.results_dir.mkdir(exist_ok=True)
        self.suites_dir.mkdir(exist_ok=True)
        
        self._init_defaults()
    
    def _init_defaults(self):
        """Initialize default data if files don't exist"""
        if not self.endpoints_file.exists():
            self._save_json(self.endpoints_file, [])
        if not self.environments_file.exists():
            self._save_json(self.environments_file, [])
    
    def _load_json(self, path: Path) -> List[Dict]:
        try:
            if path.exists():
                with open(path, 'r') as f:
                    return json.load(f)
            return []
        except Exception as e:
            print(f"Error loading {path}: {e}")
            return []
    
    def _save_json(self, path: Path, data: List[Dict]):
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            with open(path, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Error saving {path}: {e}")
    
    # Endpoints
    def get_endpoints(self) -> List[Dict]:
        return self._load_json(self.endpoints_file)
    
    def add_endpoint(self, endpoint: Endpoint) -> bool:
        endpoints = self.get_endpoints()
        endpoints.append(endpoint.dict())
        self._save_json(self.endpoints_file, endpoints)
        return True
    
    def update_endpoint(self, endpoint_id: str, endpoint: Endpoint) -> bool:
        endpoints = self.get_endpoints()
        for i, ep in enumerate(endpoints):
            if ep['id'] == endpoint_id:
                endpoints[i] = endpoint.dict()
                self._save_json(self.endpoints_file, endpoints)
                return True
        return False
    
    def delete_endpoint(self, endpoint_id: str) -> bool:
        endpoints = self.get_endpoints()
        endpoints = [ep for ep in endpoints if ep['id'] != endpoint_id]
        self._save_json(self.endpoints_file, endpoints)
        return True
    
    # Environments
    def get_environments(self) -> List[Dict]:
        return self._load_json(self.environments_file)
    
    def add_environment(self, environment: Environment) -> bool:
        environments = self.get_environments()
        environments.append(environment.dict())
        self._save_json(self.environments_file, environments)
        return True
    
    def update_environment(self, env_id: str, environment: Environment) -> bool:
        environments = self.get_environments()
        for i, env in enumerate(environments):
            if env['id'] == env_id:
                environments[i] = environment.dict()
                self._save_json(self.environments_file, environments)
                return True
        return False
    
    def delete_environment(self, env_id: str) -> bool:
        environments = self.get_environments()
        environments = [env for env in environments if env['id'] != env_id]
        self._save_json(self.environments_file, environments)
        return True
    
    # Results
    def save_result(self, suite_id: str, result: TestResult):
        result_file = self.results_dir / f"{suite_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(result_file, 'w') as f:
            json.dump(result.dict(), f, indent=2)
    
    def get_results(self, suite_id: str) -> List[Dict]:
        results = []
        for file in self.results_dir.glob(f"{suite_id}_*.json"):
            try:
                with open(file, 'r') as f:
                    results.append(json.load(f))
            except Exception as e:
                print(f"Error loading result {file}: {e}")
        return sorted(results, key=lambda r: r.get('timestamp', ''), reverse=True)
    
    # Test Suites
    def save_suite(self, suite: TestSuite):
        suite_file = self.suites_dir / f"{suite.id}.json"
        with open(suite_file, 'w') as f:
            json.dump(suite.dict(), f, indent=2)
    
    def get_suite(self, suite_id: str) -> Optional[Dict]:
        suite_file = self.suites_dir / f"{suite_id}.json"
        if suite_file.exists():
            try:
                with open(suite_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error loading suite {suite_id}: {e}")
        return None
    
    def list_suites(self) -> List[Dict]:
        suites = []
        for file in self.suites_dir.glob("*.json"):
            try:
                with open(file, 'r') as f:
                    suites.append(json.load(f))
            except Exception as e:
                print(f"Error loading suite {file}: {e}")
        return suites

# ============================================================================
# TEST EXECUTOR
# ============================================================================

class APITestExecutor:
    """Executes API tests against endpoints and environments"""
    
    def __init__(self):
        self.timeout = aiohttp.ClientTimeout(total=8)
    
    async def run_request(self, endpoint: Dict, environment: Dict) -> TestResult:
        """Execute a single API request"""
        url = environment['baseUrl'].rstrip('/') + endpoint['path']
        
        headers = {
            'Content-Type': 'application/json',
            **(environment.get('headers', {}))
        }
        
        # Add auth if configured
        if endpoint.get('auth') == 'bearer' and environment.get('token'):
            auth_token = environment['token'] if environment['token'].startswith('Bearer') else f"Bearer {environment['token']}"
            headers['Authorization'] = auth_token
        elif endpoint.get('auth') == 'apikey' and environment.get('token'):
            headers['X-API-Key'] = environment['token']
        
        # Prepare body
        body = None
        if endpoint.get('body') and endpoint['method'] in ['POST', 'PUT', 'PATCH']:
            try:
                body = json.loads(endpoint['body']) if isinstance(endpoint['body'], str) else endpoint['body']
            except:
                body = endpoint['body']
        
        start_time = asyncio.get_event_loop().time()
        status = None
        error = None
        response_body = None
        
        try:
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                method = endpoint['method'].upper()
                
                async with session.request(
                    method,
                    url,
                    json=body if body else None,
                    headers=headers
                ) as resp:
                    status = resp.status
                    try:
                        response_body = await resp.json()
                    except:
                        response_body = await resp.text()
        
        except asyncio.TimeoutError:
            error = "Timeout after 8s"
        except Exception as e:
            error = str(e)
        
        duration = int((asyncio.get_event_loop().time() - start_time) * 1000)
        
        # Determine pass/fail
        expected_codes = endpoint.get('expectedCodes', [200])
        passed = not error and status in expected_codes
        
        return TestResult(
            key=f"{endpoint['id']}::{environment['id']}",
            pass_=passed,
            status=status,
            duration=duration,
            error=error,
            url=url,
            body=response_body,
            timestamp=datetime.now().isoformat(),
            envName=environment['name'],
            epName=endpoint['name'],
            method=endpoint['method']
        )
    
    async def run_batch(self, endpoints: List[Dict], environments: List[Dict], callback=None) -> List[TestResult]:
        """Execute multiple tests with optional progress callback"""
        results = []
        total = len(endpoints) * len(environments)
        current = 0
        
        for endpoint in endpoints:
            for env in environments:
                if env['id'] not in endpoint.get('envIds', []):
                    continue
                
                result = await self.run_request(endpoint, env)
                results.append(result)
                current += 1
                
                if callback:
                    await callback({
                        'progress': current / total,
                        'current': current,
                        'total': total,
                        'result': result.dict()
                    })
        
        return results

# ============================================================================
# GLOBAL INSTANCES
# ============================================================================

storage = APIMatrixStorage()
executor = APITestExecutor()
