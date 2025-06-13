#!/usr/bin/env python3
"""
Comprehensive Test Runner for Vertex AI Grant Agent
Tests all modes, monitors performance, and validates output quality
"""

import asyncio
import aiohttp
import json
import time
import sys
from typing import Dict, Any, List
from datetime import datetime
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('test_results.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class GrantAgentTester:
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip('/')
        self.results = []
        self.session = None
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    async def test_health_check(self) -> Dict[str, Any]:
        """Test health endpoint"""
        logger.info("🏥 Testing Health Check...")
        
        start_time = time.time()
        try:
            async with self.session.get(f"{self.base_url}/health") as response:
                duration = time.time() - start_time
                data = await response.json()
                
                result = {
                    "test": "health_check",
                    "status": "PASS" if response.status == 200 else "FAIL",
                    "duration": duration,
                    "response_code": response.status,
                    "data": data
                }
                
                logger.info(f"✅ Health Check: {result['status']} ({duration:.2f}s)")
                return result
                
        except Exception as e:
            result = {
                "test": "health_check", 
                "status": "FAIL",
                "error": str(e),
                "duration": time.time() - start_time
            }
            logger.error(f"❌ Health Check Failed: {e}")
            return result

    async def test_quick_proposal(self, test_case: Dict[str, Any]) -> Dict[str, Any]:
        """Test quick proposal generation"""
        logger.info(f"🚀 Testing Quick Proposal: {test_case['name']}")
        
        start_time = time.time()
        try:
            headers = {'Content-Type': 'application/json'}
            async with self.session.post(
                f"{self.base_url}/quick_proposal",
                json=test_case['data'],
                headers=headers
            ) as response:
                duration = time.time() - start_time
                data = await response.json()
                
                # Validate response
                validation_results = self._validate_proposal_response(
                    data, test_case, duration
                )
                
                result = {
                    "test": f"quick_proposal_{test_case['name']}",
                    "status": "PASS" if validation_results['overall_pass'] else "FAIL",
                    "duration": duration,
                    "response_code": response.status,
                    "validation": validation_results,
                    "proposal_preview": data.get('proposal', '')[:200] + "..." if data.get('proposal') else None
                }
                
                logger.info(f"✅ Quick Proposal '{test_case['name']}': {result['status']} ({duration:.2f}s)")
                return result
                
        except Exception as e:
            result = {
                "test": f"quick_proposal_{test_case['name']}",
                "status": "FAIL", 
                "error": str(e),
                "duration": time.time() - start_time
            }
            logger.error(f"❌ Quick Proposal '{test_case['name']}' Failed: {e}")
            return result

    async def test_full_proposal(self, test_case: Dict[str, Any]) -> Dict[str, Any]:
        """Test full proposal generation"""
        logger.info(f"📋 Testing Full Proposal: {test_case['name']}")
        
        start_time = time.time()
        try:
            headers = {'Content-Type': 'application/json'}
            async with self.session.post(
                f"{self.base_url}/full_proposal",
                json=test_case['data'],
                headers=headers
            ) as response:
                duration = time.time() - start_time
                data = await response.json()
                
                # Validate response
                validation_results = self._validate_proposal_response(
                    data, test_case, duration
                )
                
                result = {
                    "test": f"full_proposal_{test_case['name']}",
                    "status": "PASS" if validation_results['overall_pass'] else "FAIL",
                    "duration": duration,
                    "response_code": response.status,
                    "validation": validation_results,
                    "proposal_preview": data.get('proposal', '')[:300] + "..." if data.get('proposal') else None
                }
                
                logger.info(f"✅ Full Proposal '{test_case['name']}': {result['status']} ({duration:.2f}s)")
                return result
                
        except Exception as e:
            result = {
                "test": f"full_proposal_{test_case['name']}",
                "status": "FAIL",
                "error": str(e), 
                "duration": time.time() - start_time
            }
            logger.error(f"❌ Full Proposal '{test_case['name']}' Failed: {e}")
            return result

    def _validate_proposal_response(self, data: Dict[str, Any], test_case: Dict[str, Any], duration: float) -> Dict[str, Any]:
        """Validate proposal response quality"""
        validation = {
            "has_success_flag": "success" in data,
            "success_is_true": data.get("success") == True,
            "has_proposal_text": "proposal" in data and bool(data.get("proposal")),
            "meets_length_requirement": False,
            "contains_expected_content": [],
            "has_expected_sections": [],
            "response_time_acceptable": duration < 60,  # 60 second timeout
            "overall_pass": False
        }
        
        proposal_text = data.get("proposal", "")
        
        # Check length
        min_length = test_case.get("minimum_length", 100)
        validation["meets_length_requirement"] = len(proposal_text) >= min_length
        
        # Check expected content
        expected_content = test_case.get("should_contain", [])
        for content in expected_content:
            validation["contains_expected_content"].append({
                "content": content,
                "found": content.lower() in proposal_text.lower()
            })
        
        # Check expected sections
        expected_sections = test_case.get("expected_sections", [])
        for section in expected_sections:
            validation["has_expected_sections"].append({
                "section": section, 
                "found": section.lower() in proposal_text.lower()
            })
        
        # Overall pass/fail
        validation["overall_pass"] = (
            validation["has_success_flag"] and
            validation["success_is_true"] and 
            validation["has_proposal_text"] and
            validation["meets_length_requirement"] and
            validation["response_time_acceptable"]
        )
        
        return validation

    async def run_performance_test(self, endpoint: str, data: Dict[str, Any], concurrent_requests: int = 3) -> Dict[str, Any]:
        """Run concurrent performance test"""
        logger.info(f"⚡ Performance Test: {concurrent_requests} concurrent requests to {endpoint}")
        
        async def single_request():
            start_time = time.time()
            try:
                async with self.session.post(f"{self.base_url}{endpoint}", json=data) as response:
                    await response.json()
                    return {
                        "success": True,
                        "duration": time.time() - start_time,
                        "status_code": response.status
                    }
            except Exception as e:
                return {
                    "success": False,
                    "duration": time.time() - start_time,
                    "error": str(e)
                }
        
        start_time = time.time()
        results = await asyncio.gather(*[single_request() for _ in range(concurrent_requests)])
        total_time = time.time() - start_time
        
        successful_requests = sum(1 for r in results if r["success"])
        avg_duration = sum(r["duration"] for r in results) / len(results)
        
        performance_result = {
            "test": f"performance_{endpoint.replace('/', '_')}",
            "concurrent_requests": concurrent_requests,
            "successful_requests": successful_requests,
            "total_time": total_time,
            "average_request_time": avg_duration,
            "requests_per_second": concurrent_requests / total_time,
            "status": "PASS" if successful_requests == concurrent_requests else "FAIL",
            "individual_results": results
        }
        
        logger.info(f"⚡ Performance Test: {successful_requests}/{concurrent_requests} successful ({avg_duration:.2f}s avg)")
        return performance_result

    async def run_all_tests(self, test_cases_file: str = "test_cases.json") -> Dict[str, Any]:
        """Run all test suites"""
        logger.info("🧪 Starting Comprehensive Test Suite")
        
        # Load test cases
        try:
            with open(test_cases_file, 'r') as f:
                test_data = json.load(f)
        except FileNotFoundError:
            logger.error(f"❌ Test cases file not found: {test_cases_file}")
            return {"error": "Test cases file not found"}
        
        all_results = {
            "test_run_id": datetime.now().isoformat(),
            "base_url": self.base_url,
            "health_check": None,
            "quick_proposal_tests": [],
            "full_proposal_tests": [],
            "performance_tests": [],
            "summary": {}
        }
        
        # Health check
        all_results["health_check"] = await self.test_health_check()
        
        # Quick proposal tests
        for test_case in test_data["test_cases"]["quick_proposal_tests"]:
            result = await self.test_quick_proposal(test_case)
            all_results["quick_proposal_tests"].append(result)
        
        # Full proposal tests  
        for test_case in test_data["test_cases"]["full_proposal_tests"]:
            result = await self.test_full_proposal(test_case)
            all_results["full_proposal_tests"].append(result)
        
        # Performance tests
        performance_data = {
            "organization_name": "Test Org",
            "project_title": "Performance Test",
            "funder_name": "Test Funder", 
            "amount_requested": "50000",
            "project_description": "Testing system performance under load"
        }
        
        perf_result = await self.run_performance_test("/quick_proposal", performance_data, 3)
        all_results["performance_tests"].append(perf_result)
        
        # Generate summary
        all_results["summary"] = self._generate_test_summary(all_results)
        
        return all_results

    def _generate_test_summary(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate test summary statistics"""
        summary = {
            "total_tests": 0,
            "passed_tests": 0,
            "failed_tests": 0,
            "average_response_time": 0,
            "health_status": results["health_check"]["status"] if results["health_check"] else "UNKNOWN"
        }
        
        all_test_results = (
            [results["health_check"]] + 
            results["quick_proposal_tests"] + 
            results["full_proposal_tests"] +
            results["performance_tests"]
        )
        
        durations = []
        for test_result in all_test_results:
            if test_result:
                summary["total_tests"] += 1
                if test_result["status"] == "PASS":
                    summary["passed_tests"] += 1
                else:
                    summary["failed_tests"] += 1
                
                if "duration" in test_result:
                    durations.append(test_result["duration"])
        
        summary["average_response_time"] = sum(durations) / len(durations) if durations else 0
        summary["pass_rate"] = (summary["passed_tests"] / summary["total_tests"]) * 100 if summary["total_tests"] > 0 else 0
        
        return summary

async def main():
    """Main test runner"""
    base_url = "https://vertex-grant-agent-vqjdj6kdpq-uc.a.run.app"
    
    logger.info("🚀 Starting Vertex AI Grant Agent Test Suite")
    logger.info(f"📍 Target URL: {base_url}")
    
    async with GrantAgentTester(base_url) as tester:
        results = await tester.run_all_tests()
        
        # Save results
        results_file = f"test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2)
        
        # Print summary
        summary = results["summary"]
        logger.info("📊 TEST SUMMARY")
        logger.info(f"✅ Passed: {summary['passed_tests']}/{summary['total_tests']} ({summary['pass_rate']:.1f}%)")
        logger.info(f"⏱️  Average Response Time: {summary['average_response_time']:.2f}s")
        logger.info(f"🏥 Health Status: {summary['health_status']}")
        logger.info(f"📄 Full results saved to: {results_file}")
        
        return results

if __name__ == "__main__":
    asyncio.run(main()) 