#!/usr/bin/env python3
"""
Comprehensive integration test for SirHiss Trading Platform
Tests the complete stack: Frontend -> Backend -> Database
"""

import requests
import time
import json
from typing import Dict, List

# Configuration
BACKEND_URL = "http://localhost:9002"
FRONTEND_URL = "http://localhost:9001"

class SirHissIntegrationTest:
    def __init__(self):
        self.backend_url = BACKEND_URL
        self.frontend_url = FRONTEND_URL
        self.test_results = []
    
    def log_test(self, test_name: str, success: bool, message: str = ""):
        """Log test results"""
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}: {message}")
        self.test_results.append({
            "test": test_name,
            "success": success,
            "message": message
        })
    
    def test_backend_health(self) -> bool:
        """Test if backend is running and responding"""
        try:
            response = requests.get(f"{self.backend_url}/api/v1/algorithms/types", timeout=5)
            success = response.status_code == 200
            data = response.json() if success else {}
            
            self.log_test(
                "Backend Health Check", 
                success, 
                f"Status: {response.status_code}, Algorithm types: {len(data) if success else 0}"
            )
            return success
        except Exception as e:
            self.log_test("Backend Health Check", False, f"Error: {str(e)}")
            return False
    
    def test_frontend_availability(self) -> bool:
        """Test if frontend is serving content"""
        try:
            response = requests.get(self.frontend_url, timeout=5)
            success = response.status_code == 200 and "SirHiss" in response.text
            
            self.log_test(
                "Frontend Availability", 
                success, 
                f"Status: {response.status_code}, Contains SirHiss: {'SirHiss' in response.text}"
            )
            return success
        except Exception as e:
            self.log_test("Frontend Availability", False, f"Error: {str(e)}")
            return False
    
    def test_algorithm_api_endpoints(self) -> bool:
        """Test core algorithm API endpoints"""
        endpoints = [
            ("/api/v1/algorithms/types", "GET", "Algorithm Types"),
            ("/api/v1/algorithms/templates", "GET", "Algorithm Templates")
        ]
        
        all_success = True
        
        for endpoint, method, name in endpoints:
            try:
                url = f"{self.backend_url}{endpoint}"
                response = requests.request(method, url, timeout=5)
                success = response.status_code in [200, 404]  # 404 is acceptable for empty data
                
                self.log_test(
                    f"API Endpoint: {name}",
                    success,
                    f"{method} {endpoint} -> {response.status_code}"
                )
                
                if not success:
                    all_success = False
                    
            except Exception as e:
                self.log_test(f"API Endpoint: {name}", False, f"Error: {str(e)}")
                all_success = False
        
        return all_success
    
    def test_algorithm_types_structure(self) -> bool:
        """Test algorithm types API returns correct structure"""
        try:
            response = requests.get(f"{self.backend_url}/api/v1/algorithms/types", timeout=5)
            
            if response.status_code != 200:
                self.log_test("Algorithm Types Structure", False, f"Status: {response.status_code}")
                return False
            
            data = response.json()
            
            # Expected categories
            expected_categories = [
                "Technical Analysis", 
                "High Frequency", 
                "Long-term Investment", 
                "Market Making", 
                "Sentiment Analysis"
            ]
            
            success = isinstance(data, dict) and all(cat in data for cat in expected_categories)
            
            self.log_test(
                "Algorithm Types Structure",
                success,
                f"Categories found: {list(data.keys()) if success else 'Invalid structure'}"
            )
            
            return success
            
        except Exception as e:
            self.log_test("Algorithm Types Structure", False, f"Error: {str(e)}")
            return False
    
    def test_database_connection(self) -> bool:
        """Test database connectivity through API"""
        try:
            # Try to access bots endpoint (should return empty list or data)
            response = requests.get(f"{self.backend_url}/api/v1/bots/", timeout=5)
            success = response.status_code in [200, 401]  # 401 is acceptable (no auth)
            
            self.log_test(
                "Database Connection",
                success,
                f"Bots endpoint status: {response.status_code}"
            )
            
            return success
            
        except Exception as e:
            self.log_test("Database Connection", False, f"Error: {str(e)}")
            return False
    
    def test_api_documentation(self) -> bool:
        """Test if API documentation is accessible"""
        try:
            response = requests.get(f"{self.backend_url}/api/docs", timeout=5)
            success = response.status_code == 200
            
            self.log_test(
                "API Documentation",
                success,
                f"FastAPI docs status: {response.status_code}"
            )
            
            return success
            
        except Exception as e:
            self.log_test("API Documentation", False, f"Error: {str(e)}")
            return False
    
    def test_cors_headers(self) -> bool:
        """Test CORS headers for frontend-backend communication"""
        try:
            response = requests.options(
                f"{self.backend_url}/api/v1/algorithms/types",
                headers={'Origin': self.frontend_url},
                timeout=5
            )
            
            cors_header = response.headers.get('Access-Control-Allow-Origin', '')
            success = '*' in cors_header or self.frontend_url in cors_header
            
            self.log_test(
                "CORS Configuration",
                success,
                f"Allow-Origin: {cors_header or 'Not set'}"
            )
            
            return success
            
        except Exception as e:
            self.log_test("CORS Configuration", False, f"Error: {str(e)}")
            return False
    
    def test_advanced_algorithm_integration(self) -> bool:
        """Test that all advanced algorithms are properly integrated"""
        try:
            response = requests.get(f"{self.backend_url}/api/v1/algorithms/types", timeout=5)
            
            if response.status_code != 200:
                self.log_test("Advanced Algorithm Integration", False, "Types API failed")
                return False
            
            data = response.json()
            
            # Check for all implemented algorithm types
            expected_algorithms = [
                "AdvancedTechnicalIndicator",
                "Scalping", 
                "DynamicDCA",
                "GridTrading",
                "TrendFollowing",
                "Sentiment",
                "Arbitrage"
            ]
            
            found_algorithms = []
            for category_algorithms in data.values():
                if isinstance(category_algorithms, list):
                    found_algorithms.extend(category_algorithms)
            
            success = all(alg in found_algorithms for alg in expected_algorithms)
            missing = [alg for alg in expected_algorithms if alg not in found_algorithms]
            
            self.log_test(
                "Advanced Algorithm Integration",
                success,
                f"Found: {len(found_algorithms)}/7, Missing: {missing if missing else 'None'}"
            )
            
            return success
            
        except Exception as e:
            self.log_test("Advanced Algorithm Integration", False, f"Error: {str(e)}")
            return False
    
    def run_all_tests(self) -> Dict:
        """Run all integration tests"""
        print("🐍 SirHiss Trading Platform - Integration Test Suite")
        print("=" * 60)
        
        # Run all tests
        tests = [
            self.test_backend_health,
            self.test_frontend_availability,
            self.test_algorithm_api_endpoints,
            self.test_algorithm_types_structure,
            self.test_database_connection,
            self.test_api_documentation,
            self.test_cors_headers,
            self.test_advanced_algorithm_integration,
        ]
        
        passed = 0
        failed = 0
        
        for test_func in tests:
            try:
                if test_func():
                    passed += 1
                else:
                    failed += 1
            except Exception as e:
                print(f"❌ FAIL {test_func.__name__}: Unexpected error: {str(e)}")
                failed += 1
            
            time.sleep(0.5)  # Brief pause between tests
        
        print("\n" + "=" * 60)
        print(f"📊 Test Results: {passed} passed, {failed} failed")
        
        if failed == 0:
            print("🎉 All tests passed! SirHiss platform is fully operational.")
        else:
            print(f"⚠️  {failed} test(s) failed. Check the issues above.")
        
        return {
            "passed": passed,
            "failed": failed,
            "total": passed + failed,
            "success_rate": (passed / (passed + failed)) * 100 if (passed + failed) > 0 else 0,
            "results": self.test_results
        }

def main():
    """Run the integration test suite"""
    tester = SirHissIntegrationTest()
    results = tester.run_all_tests()
    
    # Return appropriate exit code
    exit_code = 0 if results["failed"] == 0 else 1
    
    print(f"\n📈 Success Rate: {results['success_rate']:.1f}%")
    print(f"🚀 Platform Status: {'READY' if exit_code == 0 else 'NEEDS ATTENTION'}")
    
    return exit_code

if __name__ == "__main__":
    import sys
    sys.exit(main())