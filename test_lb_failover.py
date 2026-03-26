#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Advanced Load Balancer Failover Test
Test khả năng failover khi một backend bị down
"""

import requests
import time
import subprocess
import json
from datetime import datetime
from typing import Dict, List
import argparse


class FailoverTester:
    """Test failover capabilities"""
    
    def __init__(self, url: str = "http://localhost:8008", num_requests: int = 30):
        self.url = url
        self.num_requests = num_requests
        self.results = {
            "normal": {},
            "failover": {},
            "recovery": {}
        }
    
    def send_requests(self, stage: str, num: int = None) -> Dict:
        """Gửi requests và đếm responses từ mỗi backend"""
        if num is None:
            num = self.num_requests
        
        results = {"WEB1": 0, "WEB2": 0, "failed": 0}
        response_times = []
        
        print(f"\nSending {num} requests ({stage})...")
        
        for i in range(1, num + 1):
            try:
                start = time.time()
                response = requests.get(self.url, timeout=2)
                elapsed = (time.time() - start) * 1000
                response_times.append(elapsed)
                
                content = response.text
                if "WEB1" in content:
                    results["WEB1"] += 1
                    status = "WEB1"
                elif "WEB2" in content:
                    results["WEB2"] += 1
                    status = "WEB2"
                else:
                    results["failed"] += 1
                    status = "UNKNOWN"
                
                print(f"  {i:2d}. {status:7s} - {elapsed:6.1f}ms", flush=True)
                
            except Exception as e:
                results["failed"] += 1
                print(f"  {i:2d}. FAILED - {str(e)}", flush=True)
            
            time.sleep(0.2)
        
        results["avg_response_time"] = sum(response_times) / len(response_times) if response_times else 0
        return results
    
    def run_docker_command(self, command: str) -> bool:
        """Chạy docker-compose command"""
        try:
            result = subprocess.run(
                f"docker-compose {command}",
                shell=True,
                capture_output=True,
                text=True,
                timeout=10
            )
            return result.returncode == 0
        except Exception as e:
            print(f"[ERROR] Docker command failed: {e}")
            return False
    
    def test_normal_operation(self):
        """TEST 1: Hoạt động bình thường"""
        print("\n" + "="*60)
        print("[TEST 1] NORMAL OPERATION - Both backends running")
        print("="*60)
        
        self.results["normal"] = self.send_requests("Normal Operation")
        return self.results["normal"]
    
    def test_failover(self):
        """TEST 2: Failover - Dừng WEB2"""
        print("\n" + "="*60)
        print("[TEST 2] FAILOVER TEST - Stopping WEB2")
        print("="*60)
        
        print("\n[ACTION] Stopping WEB2 container...")
        if self.run_docker_command("stop web2"):
            print("[OK] WEB2 stopped successfully")
        else:
            print("[ERROR] Failed to stop WEB2")
            return None
        
        print("\nWaiting 5 seconds for nginx to detect failure...")
        time.sleep(5)
        
        self.results["failover"] = self.send_requests("Failover (WEB2 DOWN)")
        return self.results["failover"]
    
    def test_recovery(self):
        """TEST 3: Recovery - Khôi phục WEB2"""
        print("\n" + "="*60)
        print("[TEST 3] RECOVERY TEST - Starting WEB2")
        print("="*60)
        
        print("\n[ACTION] Starting WEB2 container...")
        if self.run_docker_command("start web2"):
            print("[OK] WEB2 started successfully")
        else:
            print("[ERROR] Failed to start WEB2")
            return None
        
        print("\nWaiting 5 seconds for nginx to detect recovery...")
        time.sleep(5)
        
        self.results["recovery"] = self.send_requests("Recovery (Both running)")
        return self.results["recovery"]
    
    def print_summary(self):
        """In ra bản tóm tắt"""
        print("\n" + "="*60)
        print("SUMMARY REPORT")
        print("="*60)
        
        stages = [
            ("Normal Operation", self.results["normal"]),
            ("Failover (WEB2 DOWN)", self.results["failover"]),
            ("Recovery (Both UP)", self.results["recovery"])
        ]
        
        for stage_name, results in stages:
            if not results:
                continue
            
            print(f"\n{stage_name}:")
            print(f"  WEB1:     {results['WEB1']:3d} requests ({(results['WEB1']/(results['WEB1']+results['WEB2'])*100):.1f}%)" if results['WEB1'] + results['WEB2'] > 0 else "  WEB1:     N/A")
            print(f"  WEB2:     {results['WEB2']:3d} requests ({(results['WEB2']/(results['WEB1']+results['WEB2'])*100):.1f}%)" if results['WEB1'] + results['WEB2'] > 0 else "  WEB2:     N/A")
            print(f"  Failed:   {results['failed']:3d} requests")
            print(f"  Avg Response: {results.get('avg_response_time', 0):.2f}ms")
        
        print("\n" + "="*60)
        self.print_analysis()
        print("="*60 + "\n")
    
    def print_analysis(self):
        """Phân tích kết quả test"""
        print("\nANALYSIS:")
        
        # Normal operation check
        normal = self.results["normal"]
        if normal and normal["WEB1"] > 0 and normal["WEB2"] > 0:
            print("  [OK] Normal load distribution working")
        else:
            print("  [WARNING] Normal load distribution might have issues")
        
        # Failover check
        failover = self.results["failover"]
        if failover and failover["WEB1"] > 0 and failover["WEB2"] == 0:
            print("  [OK] Failover working - traffic switched to WEB1")
        else:
            print("  [WARNING] Failover might not be working properly")
        
        # Recovery check
        recovery = self.results["recovery"]
        if recovery and recovery["WEB1"] > 0 and recovery["WEB2"] > 0:
            print("  [OK] Recovery successful - load balanced again")
        else:
            print("  [WARNING] Recovery might not be working properly")
    
    def export_report(self):
        """Xuất báo cáo JSON"""
        report = {
            "timestamp": datetime.now().isoformat(),
            "url": self.url,
            "num_requests": self.num_requests,
            "results": self.results
        }
        
        filename = f"failover_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(filename, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"\n[SAVED] Report exported to: {filename}")
        return filename


def main():
    parser = argparse.ArgumentParser(description="Load Balancer Failover Tester")
    parser.add_argument("-u", "--url", default="http://localhost:8008", help="Load balancer URL")
    parser.add_argument("-r", "--requests", type=int, default=30, help="Requests per stage")
    parser.add_argument("--no-failover", action="store_true", help="Skip failover test")
    
    args = parser.parse_args()
    
    tester = FailoverTester(args.url, args.requests)
    
    try:
        # Test normal operation
        tester.test_normal_operation()
        
        # Test failover (unless disabled)
        if not args.no_failover:
            time.sleep(2)
            tester.test_failover()
            
            # Test recovery
            time.sleep(2)
            tester.test_recovery()
        
        # Print summary
        tester.print_summary()
        
        # Export report
        tester.export_report()
        
    except KeyboardInterrupt:
        print("\n\n[INFO] Test interrupted by user")
    except Exception as e:
        print(f"\n[ERROR] Unexpected error: {e}")
    finally:
        # Make sure both containers are running
        print("[CLEANUP] Ensuring all containers are running...")
        tester.run_docker_command("start web1 web2")


if __name__ == "__main__":
    main()
