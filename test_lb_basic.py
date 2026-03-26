#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Load Balancer Test Script - Basic Version
Script kiểm tra cơ bản load balancing
"""

import requests
import time
import statistics
from collections import defaultdict
from typing import Dict, List
import argparse
from datetime import datetime


class LoadBalancerTester:
    """Class để test load balancer"""
    
    def __init__(self, url: str = "http://localhost:8008"):
        self.url = url
        self.results = defaultdict(int)
        self.response_times = []
        self.failed_requests = 0
        
    def test_connectivity(self) -> bool:
        """Kiểm tra xem load balancer có chạy không"""
        print("\n[TEST 1] Checking Load Balancer Connectivity...")
        try:
            response = requests.get(self.url, timeout=3)
            print("[OK] Load Balancer is responding")
            return True
        except Exception as e:
            print(f"[ERROR] Load Balancer is not responding: {e}")
            return False
    
    def test_load_distribution(self, total_requests: int = 20) -> Dict:
        """Test load distribution giữa các backend"""
        print(f"\n[TEST 2] Testing Load Distribution ({total_requests} requests)...")
        print("")
        
        for i in range(1, total_requests + 1):
            try:
                start_time = time.time()
                response = requests.get(self.url, timeout=3)
                elapsed = (time.time() - start_time) * 1000  # Convert to ms
                
                self.response_times.append(elapsed)
                content = response.text
                
                if "WEB1" in content:
                    self.results["WEB1"] += 1
                    print(f"Request {i:2d} -> WEB1 ({elapsed:.1f}ms)")
                elif "WEB2" in content:
                    self.results["WEB2"] += 1
                    print(f"Request {i:2d} -> WEB2 ({elapsed:.1f}ms)")
                else:
                    self.results["UNKNOWN"] += 1
                    print(f"Request {i:2d} -> UNKNOWN ({elapsed:.1f}ms)")
                    
            except Exception as e:
                self.failed_requests += 1
                print(f"Request {i:2d} -> FAILED ({str(e)})")
            
            time.sleep(0.1)  # Delay 100ms between requests
        
        return self._calculate_statistics()
    
    def _calculate_statistics(self) -> Dict:
        """Tính toán thống kê"""
        stats = {
            "total": sum(self.results.values()),
            "failed": self.failed_requests,
            "distribution": dict(self.results),
            "response_times": {
                "avg": statistics.mean(self.response_times) if self.response_times else 0,
                "min": min(self.response_times) if self.response_times else 0,
                "max": max(self.response_times) if self.response_times else 0,
            } if self.response_times else {}
        }
        return stats
    
    def print_results(self, stats: Dict) -> None:
        """In ra kết quả test"""
        print("\n" + "="*50)
        print("TEST RESULTS")
        print("="*50)
        
        print("\nDistribution:")
        for backend, count in stats["distribution"].items():
            if stats["total"] > 0:
                percentage = (count / stats["total"]) * 100
                print(f"  {backend}: {count} requests ({percentage:.1f}%)")
        
        print(f"\n  Failed: {stats['failed']} requests")
        
        if stats["response_times"]:
            print("\nResponse Times (ms):")
            print(f"  Average: {stats['response_times']['avg']:.2f}")
            print(f"  Min:     {stats['response_times']['min']:.2f}")
            print(f"  Max:     {stats['response_times']['max']:.2f}")
        
        print("\n" + "="*50)
        
        # Kiểm tra cân bằng
        if self.results["WEB1"] > 0 and self.results["WEB2"] > 0:
            print("[SUCCESS] Load balancing is working properly!")
        else:
            print("[WARNING] Load distribution might be unbalanced!")
        print("="*50 + "\n")


def main():
    parser = argparse.ArgumentParser(description="Load Balancer Tester")
    parser.add_argument("-u", "--url", default="http://localhost:8008", help="Load balancer URL")
    parser.add_argument("-r", "--requests", type=int, default=20, help="Number of requests")
    
    args = parser.parse_args()
    
    tester = LoadBalancerTester(args.url)
    
    # Test connectivity
    if not tester.test_connectivity():
        print("\nPlease start Docker containers: docker-compose up -d")
        return
    
    # Test load distribution
    stats = tester.test_load_distribution(args.requests)
    
    # Print results
    tester.print_results(stats)


if __name__ == "__main__":
    main()
