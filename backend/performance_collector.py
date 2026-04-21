"""
Performance metrics collection and analysis
Collects real-time metrics during test execution and provides analysis
"""

import json
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from collections import defaultdict
import statistics


class PerformanceDataCollector:
    """Collects and analyzes performance data from load tests"""
    
    def __init__(self):
        self.metrics: Dict[str, List[Dict]] = defaultdict(list)
        self.start_time: Optional[float] = None
        
    def record_request(self, endpoint: str, duration_ms: int, status_code: int, 
                      timestamp: float = None, success: bool = True):
        """Record a single request metric"""
        if self.start_time is None:
            self.start_time = timestamp or datetime.now().timestamp()
        
        self.metrics[endpoint].append({
            'timestamp': timestamp or datetime.now().timestamp(),
            'duration': duration_ms,
            'status': status_code,
            'success': success
        })
    
    def get_summary(self) -> Dict:
        """Get summary statistics for all endpoints"""
        summary = {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'total_duration': 0,
            'endpoints': {}
        }
        
        for endpoint, metrics in self.metrics.items():
            durations = [m['duration'] for m in metrics]
            successful = sum(1 for m in metrics if m['success'])
            failed = len(metrics) - successful
            
            summary['total_requests'] += len(metrics)
            summary['successful_requests'] += successful
            summary['failed_requests'] += failed
            
            if durations:
                summary['endpoints'][endpoint] = {
                    'total_requests': len(metrics),
                    'successful': successful,
                    'failed': failed,
                    'avg_duration': round(statistics.mean(durations), 2),
                    'min_duration': min(durations),
                    'max_duration': max(durations),
                    'median_duration': round(statistics.median(durations), 2),
                    'p95_duration': round(self._percentile(durations, 95), 2),
                    'p99_duration': round(self._percentile(durations, 99), 2),
                    'error_rate': round((failed / len(metrics)) * 100, 2) if metrics else 0,
                    'throughput': round(len(metrics) / (self._get_test_duration() or 1), 2),  # req/sec
                    'status_codes': self._count_status_codes(metrics)
                }
        
        return summary
    
    def get_timeline_data(self, endpoint: str = None) -> List[Dict]:
        """Get timeline data for charting"""
        timeline = []
        
        endpoints_to_process = [endpoint] if endpoint else self.metrics.keys()
        
        for ep in endpoints_to_process:
            metrics = self.metrics.get(ep, [])
            for metric in sorted(metrics, key=lambda x: x['timestamp']):
                timeline.append({
                    'timestamp': metric['timestamp'],
                    'endpoint': ep,
                    'duration': metric['duration'],
                    'status': metric['status'],
                    'success': metric['success']
                })
        
        return timeline
    
    def get_heatmap_data(self) -> Dict:
        """Get data for status code / endpoint heatmap"""
        heatmap = {}
        
        for endpoint, metrics in self.metrics.items():
            status_distribution = self._count_status_codes(metrics)
            total = len(metrics)
            
            heatmap[endpoint] = {
                name: (count / total) * 100 for name, count in status_distribution.items()
            }
        
        return heatmap
    
    def get_throughput_over_time(self, bucket_size_seconds: int = 5) -> Dict:
        """Get throughput data over time buckets"""
        throughput = defaultdict(lambda: defaultdict(int))
        
        for endpoint, metrics in self.metrics.items():
            for metric in metrics:
                bucket = int(metric['timestamp'] - self.start_time) // bucket_size_seconds
                throughput[endpoint][bucket] += 1
        
        return {
            ep: sorted(buckets.items())
            for ep, buckets in throughput.items()
        }
    
    def get_response_time_distribution(self, endpoint: str = None, 
                                      bins: int = 10) -> Dict:
        """Get response time distribution (histogram)"""
        endpoints_to_process = [endpoint] if endpoint else self.metrics.keys()
        distribution = {}
        
        for ep in endpoints_to_process:
            metrics = self.metrics.get(ep, [])
            durations = [m['duration'] for m in metrics]
            
            if not durations:
                continue
            
            min_duration = min(durations)
            max_duration = max(durations)
            bin_size = (max_duration - min_duration) / bins if max_duration > min_duration else 1
            
            bins_data = defaultdict(int)
            for duration in durations:
                bin_index = int((duration - min_duration) / bin_size) if bin_size > 0 else 0
                bin_index = min(bin_index, bins - 1)
                bins_data[bin_index] += 1
            
            distribution[ep] = {
                'bins': [bins_data.get(i, 0) for i in range(bins)],
                'min': min_duration,
                'max': max_duration,
                'labels': [
                    f"{min_duration + i * bin_size:.0f}-{min_duration + (i + 1) * bin_size:.0f}ms"
                    for i in range(bins)
                ]
            }
        
        return distribution
    
    @staticmethod
    def _percentile(data: List[float], percentile: int) -> float:
        """Calculate percentile"""
        if not data:
            return 0
        sorted_data = sorted(data)
        index = (percentile / 100) * (len(sorted_data) - 1)
        lower = int(index)
        upper = lower + 1
        
        if upper >= len(sorted_data):
            return float(sorted_data[lower])
        
        fraction = index - lower
        return sorted_data[lower] * (1 - fraction) + sorted_data[upper] * fraction
    
    @staticmethod
    def _count_status_codes(metrics: List[Dict]) -> Dict[str, int]:
        """Count occurrences of each status code"""
        status_counts = defaultdict(int)
        for metric in metrics:
            status_counts[f"{metric['status']}"] += 1
        return dict(status_counts)
    
    def _get_test_duration(self) -> float:
        """Get total test duration in seconds"""
        if not self.start_time or not self.metrics:
            return 0
        
        all_timestamps = []
        for metrics in self.metrics.values():
            all_timestamps.extend([m['timestamp'] for m in metrics])
        
        if all_timestamps:
            return max(all_timestamps) - self.start_time
        
        return 0
    
    def export_json(self, file_path: str):
        """Export all metrics to JSON file"""
        data = {
            'summary': self.get_summary(),
            'timeline': self.get_timeline_data(),
            'heatmap': self.get_heatmap_data(),
            'throughput_over_time': self.get_throughput_over_time(),
            'response_time_distribution': self.get_response_time_distribution(),
            'exported_at': datetime.now().isoformat()
        }
        
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=2, default=str)
    
    def clear(self):
        """Clear all collected metrics"""
        self.metrics.clear()
        self.start_time = None
