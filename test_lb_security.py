#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Security Testing - Load Balancer Penetration Test
Script kiểm tra security aspects của load balancer
"""

import requests
import time
import json
from datetime import datetime
from typing import Dict, List
import argparse
from urllib.parse import quote


class LoadBalancerSecurityTester:
    """Test security aspects của load balancer"""
    
    def __init__(self, url: str = "http://localhost:8008"):
        self.url = url
        self.results = {}
        self.headers_baseline = None
    
    def test_backend_detection(self) -> Dict:
        """TEST 1: Phát hiện backend identification"""
        print("\n[TEST 1] Backend Detection & Fingerprinting")
        print("="*60)
        
        findings = {"headers": {}, "body": {}, "timing": []}
        
        for i in range(5):
            try:
                response = requests.get(self.url, timeout=3)
                
                # Kiểm tra headers
                findings["headers"].update({
                    "Server": response.headers.get("Server", "N/A"),
                    "X-Powered-By": response.headers.get("X-Powered-By", "N/A"),
                    "X-Real-IP": response.headers.get("X-Real-IP", "N/A"),
                    "X-Forwarded-For": response.headers.get("X-Forwarded-For", "N/A"),
                })
                
                # Kiểm tra body (backend identifier)
                if "WEB1" in response.text:
                    print(f"  Request {i+1}: Backend = WEB1 (detected from body)")
                    findings["body"]["backend"] = "WEB1"
                elif "WEB2" in response.text:
                    print(f"  Request {i+1}: Backend = WEB2 (detected from body)")
                    findings["body"]["backend"] = "WEB2"
                
                findings["timing"].append(response.elapsed.total_seconds() * 1000)
                
            except Exception as e:
                print(f"  Request {i+1}: ERROR - {e}")
        
        print("\nDetected Headers:")
        for key, value in findings["headers"].items():
            if value != "N/A":
                print(f"  {key}: {value}")
                if "nginx" in str(value).lower():
                    print("    -> [FINDING] Nginx detected!")
        
        self.results["backend_detection"] = findings
        return findings
    
    def test_header_injection(self) -> Dict:
        """TEST 2: Header injection & manipulation"""
        print("\n[TEST 2] Header Injection Testing")
        print("="*60)
        
        findings = {}
        
        injection_payloads = {
            "X-Original-URL": "/admin",
            "X-Forwarded-Host": "evil.com",
            "X-Client-IP": "127.0.0.1",
            "X-Real-IP": "127.0.0.1",
        }
        
        for header, payload in injection_payloads.items():
            try:
                headers = {header: payload}
                response = requests.get(self.url, headers=headers, timeout=3)
                
                print(f"  {header}: {payload}")
                print(f"    Status: {response.status_code}")
                print(f"    Response size: {len(response.content)} bytes")
                
                if response.status_code != 200:
                    findings[header] = f"Status changed to {response.status_code}"
                    print(f"    -> [FINDING] Status code changed!")
                
            except Exception as e:
                print(f"  {header}: ERROR - {e}")
        
        self.results["header_injection"] = findings
        return findings
    
    def test_path_traversal(self) -> Dict:
        """TEST 3: Path traversal & directory enumeration"""
        print("\n[TEST 3] Path Traversal Testing")
        print("="*60)
        
        findings = {"accessible_paths": [], "errors": []}
        
        paths = [
            "/",
            "/admin",
            "/admin/",
            "/../",
            "/..%2f",
            "/...%2f...%2f",
            "/etc/passwd",
            "/%2e%2e/%2e%2e/etc/passwd",
        ]
        
        for path in paths:
            try:
                response = requests.get(self.url + path, timeout=3)
                print(f"  {path}: {response.status_code}")
                
                if response.status_code == 200:
                    findings["accessible_paths"].append(path)
                
                if "error" in response.text.lower() or "not found" in response.text.lower():
                    findings["errors"].append(path)
                
            except Exception as e:
                print(f"  {path}: ERROR")
        
        print(f"\nAccessible paths: {len(findings['accessible_paths'])}")
        self.results["path_traversal"] = findings
        return findings
    
    def test_sql_injection_reflection(self) -> Dict:
        """TEST 4: SQL injection indicators"""
        print("\n[TEST 4] SQL Injection Testing (Detection)")
        print("="*60)
        
        findings = {"reflected": [], "errors": []}
        
        payloads = [
            "' OR '1'='1",
            "1' UNION SELECT NULL--",
            "admin' --",
            "1'; DROP TABLE users--",
        ]
        
        for payload in payloads:
            try:
                response = requests.get(
                    self.url + "?id=" + quote(payload),
                    timeout=3
                )
                
                print(f"  Payload: {payload}")
                print(f"    Status: {response.status_code}")
                
                if payload in response.text:
                    findings["reflected"].append(payload)
                    print(f"    -> [FINDING] Payload reflected in response!")
                
                if any(err in response.text.lower() for err in ["sql", "syntax", "error"]):
                    findings["errors"].append(payload)
                    print(f"    -> [FINDING] SQL error detected!")
                
            except Exception as e:
                print(f"  Payload: ERROR")
        
        self.results["sql_injection"] = findings
        return findings
    
    def test_response_headers_security(self) -> Dict:
        """TEST 5: Security headers check"""
        print("\n[TEST 5] Security Headers Verification")
        print("="*60)
        
        findings = {"present": [], "missing": []}
        
        security_headers = [
            "Strict-Transport-Security",
            "X-Content-Type-Options",
            "X-Frame-Options",
            "X-XSS-Protection",
            "Content-Security-Policy",
            "Access-Control-Allow-Origin",
        ]
        
        try:
            response = requests.get(self.url, timeout=3)
            
            for header in security_headers:
                if header in response.headers:
                    value = response.headers[header]
                    findings["present"].append({header: value})
                    print(f"  [+] {header}: {value}")
                else:
                    findings["missing"].append(header)
                    print(f"  [-] {header}: MISSING")
            
        except Exception as e:
            print(f"  ERROR: {e}")
        
        print(f"\nSecurity Headers: {len(findings['present'])}/{len(security_headers)}")
        self.results["security_headers"] = findings
        return findings
    
    def test_timing_attacks(self) -> Dict:
        """TEST 6: Timing attack detection"""
        print("\n[TEST 6] Timing Attack Testing")
        print("="*60)
        
        findings = {"timings": [], "variance": 0}
        
        payloads = [
            "",
            "' OR 1=1--",
            "' OR 1=1/*",
            "admin' --",
        ]
        
        print("Testing response times for different payloads...\n")
        
        for payload in payloads:
            times = []
            for i in range(5):
                try:
                    start = time.time()
                    response = requests.get(
                        self.url + "?id=" + quote(payload),
                        timeout=3
                    )
                    elapsed = (time.time() - start) * 1000
                    times.append(elapsed)
                except:
                    pass
            
            avg_time = sum(times) / len(times) if times else 0
            findings["timings"].append({
                "payload": payload if payload else "[empty]",
                "avg_ms": avg_time
            })
            print(f"  Payload: {payload if payload else '[empty]'}")
            print(f"    Average: {avg_time:.2f}ms")
        
        self.results["timing_attacks"] = findings
        return findings
    
    def print_security_report(self):
        """In ra security report"""
        print("\n" + "="*60)
        print("SECURITY TEST REPORT")
        print("="*60)
        print(f"\nTarget: {self.url}")
        print(f"Timestamp: {datetime.now().isoformat()}")
        
        print("\nFindings Summary:")
        
        # Backend detection
        bd = self.results.get("backend_detection", {})
        print(f"\n1. Backend Detection:")
        if bd.get("headers"):
            print(f"   Headers: {len(bd['headers'])} detected")
        if bd.get("body"):
            print(f"   Body: Backend identifier found")
        
        # Header injection
        hi = self.results.get("header_injection", {})
        print(f"\n2. Header Injection:")
        if hi:
            print(f"   Potential issues: {len(hi)}")
        
        # Path traversal
        pt = self.results.get("path_traversal", {})
        print(f"\n3. Path Traversal:")
        print(f"   Accessible paths: {len(pt.get('accessible_paths', []))}")
        
        # SQL injection
        si = self.results.get("sql_injection", {})
        print(f"\n4. SQL Injection:")
        print(f"   Reflected payloads: {len(si.get('reflected', []))}")
        print(f"   SQL errors: {len(si.get('errors', []))}")
        
        # Security headers
        sh = self.results.get("security_headers", {})
        print(f"\n5. Security Headers:")
        print(f"   Present: {len(sh.get('present', []))}")
        print(f"   Missing: {len(sh.get('missing', []))}")
        
        print("\n" + "="*60)
    
    def export_findings(self):
        """Xuất findings"""
        report = {
            "timestamp": datetime.now().isoformat(),
            "url": self.url,
            "findings": self.results
        }
        
        filename = f"security_findings_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(filename, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"\n[SAVED] Findings exported to: {filename}")
        return filename


def main():
    parser = argparse.ArgumentParser(description="Load Balancer Security Tester")
    parser.add_argument("-u", "--url", default="http://localhost:8008", help="Target URL")
    parser.add_argument("--all", action="store_true", help="Run all tests")
    parser.add_argument("--backend", action="store_true", help="Backend detection test")
    parser.add_argument("--headers", action="store_true", help="Header injection test")
    parser.add_argument("--paths", action="store_true", help="Path traversal test")
    parser.add_argument("--sql", action="store_true", help="SQL injection test")
    parser.add_argument("--security", action="store_true", help="Security headers test")
    parser.add_argument("--timing", action="store_true", help="Timing attack test")
    
    args = parser.parse_args()
    
    print("\n" + "="*60)
    print("LOAD BALANCER SECURITY TESTER")
    print("="*60 + "\n")
    
    tester = LoadBalancerSecurityTester(args.url)
    
    # If no specific test, run all
    run_all = args.all or not any([args.backend, args.headers, args.paths, args.sql, args.security, args.timing])
    
    try:
        if run_all or args.backend:
            tester.test_backend_detection()
        
        if run_all or args.headers:
            tester.test_header_injection()
        
        if run_all or args.paths:
            tester.test_path_traversal()
        
        if run_all or args.sql:
            tester.test_sql_injection_reflection()
        
        if run_all or args.security:
            tester.test_response_headers_security()
        
        if run_all or args.timing:
            tester.test_timing_attacks()
        
        tester.print_security_report()
        tester.export_findings()
        
    except KeyboardInterrupt:
        print("\n[INFO] Test interrupted by user")
    except Exception as e:
        print(f"\n[ERROR] Test failed: {e}")


if __name__ == "__main__":
    main()
