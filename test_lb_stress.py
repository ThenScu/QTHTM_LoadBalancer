#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Advanced Load Balancer Stress Test & Metrics
Script kiểm tra performance, response time, và stress test
"""

import requests
import time
import json
import threading
from datetime import datetime
from typing import Dict, List
import argparse
import statistics
from urllib.parse import urlparse


class StressTester:
    """Stress test load balancer"""
    
    def __init__(self, url: str = "http://localhost:8008", duration: int = 60):
        self.url = url
        self.duration = duration
        self.total_requests = 0
        self.successful_requests = 0
        self.failed_requests = 0
        self.response_times = []
        self.backend_distribution = {"WEB1": 0, "WEB2": 0, "UNKNOWN": 0}
        self.start_time = None
        self.end_time = None
        self.lock = threading.Lock()
    
    def single_request(self) -> bool:
        """Gửi một request"""
        try:
            start = time.time()
            response = requests.get(self.url, timeout=3)
            elapsed = (time.time() - start) * 1000
            
            with self.lock:
                self.total_requests += 1
                self.successful_requests += 1
                self.response_times.append(elapsed)
                
                content = response.text
                if "WEB1" in content:
                    self.backend_distribution["WEB1"] += 1
                elif "WEB2" in content:
                    self.backend_distribution["WEB2"] += 1
                else:
                    self.backend_distribution["UNKNOWN"] += 1
            
            return True
        except Exception:
            with self.lock:
                self.total_requests += 1
                self.failed_requests += 1
            return False
    
    def worker_thread(self, requests_per_second: float = 5):
        """Thread worker - gửi requests liên tục"""
        delay = 1.0 / requests_per_second
        
        while time.time() - self.start_time < self.duration:
            self.single_request()
            time.sleep(delay)
    
    def run_concurrent_test(self, num_threads: int = 5, requests_per_second: float = 5):
        """Chạy stress test với multiple threads"""
        print(f"\n[STRESS TEST] Starting with {num_threads} threads, {requests_per_second} req/s each")
        print(f"Duration: {self.duration} seconds\n")
        
        self.start_time = time.time()
        
        threads = []
        for i in range(num_threads):
            t = threading.Thread(target=self.worker_thread, args=(requests_per_second,))
            t.daemon = True
            t.start()
            threads.append(t)
        
        # Progress indicator
        last_count = 0
        while time.time() - self.start_time < self.duration:
            elapsed = time.time() - self.start_time
            if self.total_requests > last_count:
                print(f"[{elapsed:.1f}s] {self.total_requests} requests | "
                      f"WEB1: {self.backend_distribution['WEB1']:3d} | "
                      f"WEB2: {self.backend_distribution['WEB2']:3d} | "
                      f"Failed: {self.failed_requests:3d}", flush=True)
                last_count = self.total_requests
            time.sleep(1)
        
        # Wait for all threads
        for t in threads:
            t.join(timeout=5)
        
        self.end_time = time.time()
    
    def calculate_metrics(self) -> Dict:
        """Tính toán metrics chi tiết"""
        elapsed = self.end_time - self.start_time if self.end_time else 0
        
        metrics = {
            "duration": elapsed,
            "total_requests": self.total_requests,
            "successful": self.successful_requests,
            "failed": self.failed_requests,
            "success_rate": (self.successful_requests / self.total_requests * 100) if self.total_requests > 0 else 0,
            "throughput": self.total_requests / elapsed if elapsed > 0 else 0,
            "backend_distribution": self.backend_distribution,
        }
        
        if self.response_times:
            metrics["response_time"] = {
                "min": min(self.response_times),
                "max": max(self.response_times),
                "avg": statistics.mean(self.response_times),
                "median": statistics.median(self.response_times),
                "p95": sorted(self.response_times)[int(len(self.response_times) * 0.95)] if len(self.response_times) > 0 else 0,
                "p99": sorted(self.response_times)[int(len(self.response_times) * 0.99)] if len(self.response_times) > 0 else 0,
                "stdev": statistics.stdev(self.response_times) if len(self.response_times) > 1 else 0,
            }
        
        return metrics
    
    def print_metrics(self, metrics: Dict):
        """In metrics chi tiết"""
        print("\n" + "="*70)
        print("PERFORMANCE METRICS")
        print("="*70)
        
        print(f"\nTest Duration: {metrics['duration']:.2f} seconds")
        
        print("\nRequest Statistics:")
        print(f"  Total Requests:    {metrics['total_requests']:,}")
        print(f"  Successful:        {metrics['successful']:,}")
        print(f"  Failed:            {metrics['failed']:,}")
        print(f"  Success Rate:      {metrics['success_rate']:.2f}%")
        
        print("\nThroughput:")
        print(f"  Requests/second:   {metrics['throughput']:.2f}")
        
        print("\nBackend Distribution:")
        total = metrics['backend_distribution']['WEB1'] + metrics['backend_distribution']['WEB2']
        if total > 0:
            web1_pct = (metrics['backend_distribution']['WEB1'] / total * 100)
            web2_pct = (metrics['backend_distribution']['WEB2'] / total * 100)
        else:
            web1_pct = web2_pct = 0
        
        print(f"  WEB1:              {metrics['backend_distribution']['WEB1']:,} ({web1_pct:.1f}%)")
        print(f"  WEB2:              {metrics['backend_distribution']['WEB2']:,} ({web2_pct:.1f}%)")
        print(f"  Unknown:           {metrics['backend_distribution']['UNKNOWN']:,}")
        
        if "response_time" in metrics:
            print("\nResponse Times (ms):")
            rt = metrics['response_time']
            print(f"  Min:               {rt['min']:.2f}")
            print(f"  Max:               {rt['max']:.2f}")
            print(f"  Average:           {rt['avg']:.2f}")
            print(f"  Median:            {rt['median']:.2f}")
            print(f"  Std Dev:           {rt['stdev']:.2f}")
            print(f"  P95:               {rt['p95']:.2f}")
            print(f"  P99:               {rt['p99']:.2f}")
        
        print("\n" + "="*70)
        self.print_recommendations(metrics)
        print("="*70 + "\n")
    
    def print_recommendations(self, metrics: Dict):
        """In ra khuyến cáo dựa trên kết quả"""
        print("\nRECOMMENDATIONS:")
        
        if metrics['success_rate'] < 95:
            print(f"  [WARNING] Low success rate ({metrics['success_rate']:.1f}%). Check logs!")
        else:
            print(f"  [OK] Success rate is good ({metrics['success_rate']:.1f}%)")
        
        if "response_time" in metrics:
            avg_rt = metrics['response_time']['avg']
            if avg_rt > 100:
                print(f"  [WARNING] High average response time ({avg_rt:.1f}ms)")
            else:
                print(f"  [OK] Response time is good ({avg_rt:.1f}ms)")
        
        # Check load distribution
        total = metrics['backend_distribution']['WEB1'] + metrics['backend_distribution']['WEB2']
        if total > 0:
            imbalance = abs(metrics['backend_distribution']['WEB1'] - metrics['backend_distribution']['WEB2'])
            imbalance_pct = (imbalance / total * 100)
            
            if imbalance_pct > 20:
                print(f"  [WARNING] Unbalanced load distribution ({imbalance_pct:.1f}% difference)")
            else:
                print(f"  [OK] Load is balanced ({imbalance_pct:.1f}% difference)")
    
    def export_json(self, metrics: Dict) -> str:
        """Xuất báo cáo JSON"""
        report = {
            "timestamp": datetime.now().isoformat(),
            "url": self.url,
            "configuration": {
                "duration": self.duration,
            },
            "metrics": metrics
        }
        
        filename = f"stress_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(filename, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"[SAVED] Report exported to: {filename}")
        return filename


def main():
    parser = argparse.ArgumentParser(description="Load Balancer Stress Tester")
    parser.add_argument("-u", "--url", default="http://localhost:8008", help="Load balancer URL")
    parser.add_argument("-d", "--duration", type=int, default=60, help="Test duration in seconds")
    parser.add_argument("-t", "--threads", type=int, default=5, help="Number of threads")
    parser.add_argument("-r", "--rate", type=float, default=5, help="Requests per second per thread")
    
    args = parser.parse_args()
    
    print("\n" + "="*70)
    print("LOAD BALANCER STRESS TEST")
    print("="*70)
    print(f"Target: {args.url}")
    print(f"Duration: {args.duration} seconds")
    print(f"Threads: {args.threads}")
    print(f"Rate: {args.rate} req/s per thread")
    
    tester = StressTester(args.url, args.duration)
    
    try:
        tester.run_concurrent_test(args.threads, args.rate)
        metrics = tester.calculate_metrics()
        tester.print_metrics(metrics)
        tester.export_json(metrics)
        
    except KeyboardInterrupt:
        print("\n[INFO] Test interrupted by user")
    except Exception as e:
        print(f"\n[ERROR] Test failed: {e}")


if __name__ == "__main__":
    main()
