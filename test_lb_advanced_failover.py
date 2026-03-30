#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Advanced Failover Stress Test - Kịch bản kiểm tra failover dưới tải
Kịch bản:
  1. Stress test bình thường (WEB1 + WEB2)
  2. Stop WEB1 → Stress test (chỉ WEB2)
  3. Start WEB1 + Stop WEB2 → Stress test (chỉ WEB1)
  4. Start WEB2 → Stress test (WEB1 + WEB2 lại)
"""

import requests
import time
import json
import threading
import subprocess
from datetime import datetime
from typing import Dict, List
import argparse
import statistics


class AdvancedFailoverTester:
    """Advanced failover stress test"""
    
    def __init__(self, url: str = "http://localhost:8008", stage_duration: int = 30):
        self.url = url
        self.stage_duration = stage_duration
        self.results = []
        self.lock = threading.Lock()
    
    def run_docker_command(self, command: str) -> bool:
        """Chạy docker-compose command"""
        try:
            full_cmd = f"docker-compose {command}"
            result = subprocess.run(full_cmd, shell=True, capture_output=True, text=True, timeout=10)
            return result.returncode == 0
        except Exception as e:
            print(f"[ERROR] Docker command failed: {e}")
            return False
    
    def run_stress_test(self, stage_name: str, duration: int, threads: int = 3, rate: float = 5) -> Dict:
        """Chạy stress test cho một stage"""
        print(f"\n  [TEST] Starting stress test: {stage_name} ({duration}s)")
        
        total_requests = 0
        successful_requests = 0
        failed_requests = 0
        response_times = []
        backend_distribution = {"WEB1": 0, "WEB2": 0, "UNKNOWN": 0}
        
        def worker():
            nonlocal total_requests, successful_requests, failed_requests
            delay = 1.0 / rate
            start_time = time.time()
            
            while time.time() - start_time < duration:
                try:
                    req_start = time.time()
                    response = requests.get(self.url, timeout=3)
                    elapsed = (time.time() - req_start) * 1000
                    
                    with self.lock:
                        total_requests += 1
                        successful_requests += 1
                        response_times.append(elapsed)
                        
                        content = response.text
                        if "WEB1" in content:
                            backend_distribution["WEB1"] += 1
                        elif "WEB2" in content:
                            backend_distribution["WEB2"] += 1
                        else:
                            backend_distribution["UNKNOWN"] += 1
                except Exception:
                    with self.lock:
                        total_requests += 1
                        failed_requests += 1
                
                time.sleep(delay)
        
        # Run threads
        thread_list = []
        for i in range(threads):
            t = threading.Thread(target=worker)
            t.daemon = True
            t.start()
            thread_list.append(t)
        
        # Progress
        last_count = 0
        test_start = time.time()
        while time.time() - test_start < duration:
            if total_requests > last_count:
                elapsed = time.time() - test_start
                print(f"    [{elapsed:.0f}s] {total_requests:4d} req | "
                      f"WEB1: {backend_distribution['WEB1']:3d} | "
                      f"WEB2: {backend_distribution['WEB2']:3d} | "
                      f"Failed: {failed_requests:2d}", flush=True)
                last_count = total_requests
            time.sleep(1)
        
        # Wait
        for t in thread_list:
            t.join(timeout=5)
        
        # Calculate metrics
        metrics = {
            "stage": stage_name,
            "total_requests": total_requests,
            "successful": successful_requests,
            "failed": failed_requests,
            "success_rate": (successful_requests / total_requests * 100) if total_requests > 0 else 0,
            "throughput": total_requests / duration if duration > 0 else 0,
            "backend_distribution": backend_distribution,
        }
        
        if response_times:
            metrics["response_time"] = {
                "min": min(response_times),
                "max": max(response_times),
                "avg": statistics.mean(response_times),
                "p95": sorted(response_times)[int(len(response_times) * 0.95)] if len(response_times) > 0 else 0,
                "p99": sorted(response_times)[int(len(response_times) * 0.99)] if len(response_times) > 0 else 0,
            }
        
        return metrics
    
    def run_scenario(self, num_threads: int = 3, rate: float = 5):
        """Chạy kịch bản failover stress test đầy đủ"""
        print("\n" + "="*80)
        print("ADVANCED FAILOVER STRESS TEST")
        print("="*80)
        print(f"Target: {self.url}")
        print(f"Stage Duration: {self.stage_duration}s | Threads: {num_threads} | Rate: {rate} req/s")
        print("="*80)
        
        # Stage 1: Normal operation (WEB1 + WEB2)
        print("\n[STAGE 1] Normal Operation (WEB1 + WEB2)")
        print("-" * 80)
        result1 = self.run_stress_test("Normal (WEB1+WEB2)", self.stage_duration, num_threads, rate)
        self.results.append(result1)
        
        # Stage 2: WEB1 down (only WEB2)
        print("\n[STAGE 2] Failover - Stopping WEB1")
        print("-" * 80)
        print("  [ACTION] Stopping web1 container...")
        if self.run_docker_command("stop web1"):
            print("  [OK] WEB1 stopped")
            time.sleep(2)  # Wait for nginx to detect
            result2 = self.run_stress_test("WEB1 Down (WEB2 only)", self.stage_duration, num_threads, rate)
            self.results.append(result2)
        else:
            print("  [ERROR] Failed to stop WEB1")
            return False
        
        # Stage 3: WEB1 back + WEB2 down (only WEB1)
        print("\n[STAGE 3] Recovery & New Failover - Starting WEB1, Stopping WEB2")
        print("-" * 80)
        print("  [ACTION] Starting web1 container...")
        if self.run_docker_command("start web1"):
            print("  [OK] WEB1 started")
            time.sleep(2)
        
        print("  [ACTION] Stopping web2 container...")
        if self.run_docker_command("stop web2"):
            print("  [OK] WEB2 stopped")
            time.sleep(2)
            result3 = self.run_stress_test("WEB2 Down (WEB1 only)", self.stage_duration, num_threads, rate)
            self.results.append(result3)
        else:
            print("  [ERROR] Failed to stop WEB2")
            return False
        
        # Stage 4: Full recovery (WEB1 + WEB2)
        print("\n[STAGE 4] Full Recovery - Starting WEB2")
        print("-" * 80)
        print("  [ACTION] Starting web2 container...")
        if self.run_docker_command("start web2"):
            print("  [OK] WEB2 started")
            time.sleep(2)
            result4 = self.run_stress_test("Full Recovery (WEB1+WEB2)", self.stage_duration, num_threads, rate)
            self.results.append(result4)
        else:
            print("  [ERROR] Failed to start WEB2")
            return False
        
        return True
    
    def print_summary(self):
        """In tóm tắt tất cả stages"""
        print("\n" + "="*80)
        print("FAILOVER STRESS TEST SUMMARY")
        print("="*80)
        
        for result in self.results:
            print(f"\n[STAGE] {result['stage']}")
            print("-" * 80)
            print(f"  Total Requests:     {result['total_requests']:,}")
            print(f"  Successful:         {result['successful']:,}")
            print(f"  Failed:             {result['failed']:,}")
            print(f"  Success Rate:       {result['success_rate']:.2f}%")
            print(f"  Throughput:         {result['throughput']:.2f} req/s")
            
            # Backend distribution
            total = result['backend_distribution']['WEB1'] + result['backend_distribution']['WEB2']
            if total > 0:
                web1_pct = (result['backend_distribution']['WEB1'] / total * 100)
                web2_pct = (result['backend_distribution']['WEB2'] / total * 100)
            else:
                web1_pct = web2_pct = 0
            
            print(f"  Backend Distribution:")
            print(f"    WEB1:             {result['backend_distribution']['WEB1']:,} ({web1_pct:.1f}%)")
            print(f"    WEB2:             {result['backend_distribution']['WEB2']:,} ({web2_pct:.1f}%)")
            
            if "response_time" in result:
                rt = result['response_time']
                print(f"  Response Times (ms):")
                print(f"    Min:              {rt['min']:.2f}")
                print(f"    Avg:              {rt['avg']:.2f}")
                print(f"    Max:              {rt['max']:.2f}")
                print(f"    P95:              {rt['p95']:.2f}")
                print(f"    P99:              {rt['p99']:.2f}")
        
        print("\n" + "="*80)
        self.print_analysis()
        print("="*80 + "\n")
    
    def print_analysis(self):
        """Phân tích kết quả"""
        print("\nANALYSIS:")
        
        if len(self.results) < 4:
            print("  [ERROR] Not enough stages completed")
            return
        
        normal = self.results[0]
        web1_down = self.results[1]
        web2_down = self.results[2]
        recovery = self.results[3]
        
        # Check failover effectiveness
        print("\n  Failover Effectiveness:")
        
        # Stage 1 vs Stage 2 (WEB1 down)
        success_rate_drop = normal['success_rate'] - web1_down['success_rate']
        if web1_down['success_rate'] > 90:
            print(f"    ✅ WEB1 failover: Success rate maintained at {web1_down['success_rate']:.1f}%")
        else:
            print(f"    ❌ WEB1 failover: Success rate dropped to {web1_down['success_rate']:.1f}%")
        
        # Stage 3 (WEB2 down)
        if web2_down['success_rate'] > 90:
            print(f"    ✅ WEB2 failover: Success rate maintained at {web2_down['success_rate']:.1f}%")
        else:
            print(f"    ❌ WEB2 failover: Success rate dropped to {web2_down['success_rate']:.1f}%")
        
        # Stage 4 (Recovery)
        if recovery['success_rate'] > 90:
            print(f"    ✅ Recovery: Success rate restored to {recovery['success_rate']:.1f}%")
        else:
            print(f"    ❌ Recovery: Success rate only at {recovery['success_rate']:.1f}%")
        
        # Load distribution analysis
        print("\n  Load Distribution Analysis:")
        
        # Normal - should be 50-50
        normal_total = normal['backend_distribution']['WEB1'] + normal['backend_distribution']['WEB2']
        normal_web1_pct = (normal['backend_distribution']['WEB1'] / normal_total * 100) if normal_total > 0 else 0
        
        if 40 <= normal_web1_pct <= 60:
            print(f"    ✅ Normal operation: {normal_web1_pct:.1f}% WEB1 - Balanced")
        else:
            print(f"    ⚠️  Normal operation: {normal_web1_pct:.1f}% WEB1 - Unbalanced")
        
        # Web1 down - all to WEB2
        web1_down_total = web1_down['backend_distribution']['WEB1'] + web1_down['backend_distribution']['WEB2']
        web1_down_web2_pct = (web1_down['backend_distribution']['WEB2'] / web1_down_total * 100) if web1_down_total > 0 else 0
        
        if web1_down_web2_pct > 95:
            print(f"    ✅ WEB1 down: {web1_down_web2_pct:.1f}% to WEB2 - Correct")
        else:
            print(f"    ⚠️  WEB1 down: {web1_down_web2_pct:.1f}% to WEB2 - Unexpected routing")
        
        # Web2 down - all to WEB1
        web2_down_total = web2_down['backend_distribution']['WEB1'] + web2_down['backend_distribution']['WEB2']
        web2_down_web1_pct = (web2_down['backend_distribution']['WEB1'] / web2_down_total * 100) if web2_down_total > 0 else 0
        
        if web2_down_web1_pct > 95:
            print(f"    ✅ WEB2 down: {web2_down_web1_pct:.1f}% to WEB1 - Correct")
        else:
            print(f"    ⚠️  WEB2 down: {web2_down_web1_pct:.1f}% to WEB1 - Unexpected routing")
    
    def export_json(self):
        """Xuất báo cáo JSON"""
        report = {
            "timestamp": datetime.now().isoformat(),
            "url": self.url,
            "configuration": {
                "stage_duration": self.stage_duration,
            },
            "results": self.results
        }
        
        filename = f"failover_stress_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(filename, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"[SAVED] Report exported to: {filename}")


def main():
    parser = argparse.ArgumentParser(description="Advanced Failover Stress Tester")
    parser.add_argument("-u", "--url", default="http://localhost:8008", help="Load balancer URL")
    parser.add_argument("-d", "--duration", type=int, default=30, help="Duration per stage in seconds")
    parser.add_argument("-t", "--threads", type=int, default=3, help="Number of threads")
    parser.add_argument("-r", "--rate", type=float, default=5, help="Requests per second per thread")
    
    args = parser.parse_args()
    
    tester = AdvancedFailoverTester(args.url, args.duration)
    
    try:
        if tester.run_scenario(args.threads, args.rate):
            tester.print_summary()
            tester.export_json()
        else:
            print("\n[ERROR] Test scenario failed")
    except KeyboardInterrupt:
        print("\n[INFO] Test interrupted by user")
        print("[ACTION] Attempting to restore all containers...")
        tester.run_docker_command("start web1")
        tester.run_docker_command("start web2")
    except Exception as e:
        print(f"\n[ERROR] Test failed: {e}")
        print("[ACTION] Attempting to restore all containers...")
        tester.run_docker_command("start web1")
        tester.run_docker_command("start web2")


if __name__ == "__main__":
    main()
