from langchain_core.messages import HumanMessage, SystemMessage
from langchain_groq import ChatGroq
from typing import Dict, List
import subprocess
import tempfile
import os
import json
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CorrectnessAgent:
    """
    Simple Reflex + Goal-Based Agent
    Goal: Ensure code passes all tests
    Actions: Run test suites, validate outputs
    """
    
    def __init__(self, groq_api_key: str, model: str = "llama-3.1-8b-instant"):
        self.llm = ChatGroq(
            api_key=groq_api_key,
            model=model,
            temperature=0.1
        )
        self.test_results = {}
        
    async def review(self, code: str, language: str, test_cases: List[Dict] = None) -> Dict:
        """
        Review code correctness by running tests
        """
        logger.info(f"Starting correctness review for {language} code")
        
        results = {
            "tests_passed": 0,
            "total_tests": 0,
            "test_results": [],
            "errors": [],
            "summary": ""
        }
        
        # Generate test cases if not provided
        if not test_cases:
            test_cases = await self._generate_test_cases(code, language)
            results["total_tests"] = len(test_cases)
        
        # Run tests based on language
        if language == "python":
            test_results = await self._run_python_tests(code, test_cases)
        elif language == "javascript":
            test_results = await self._run_javascript_tests(code, test_cases)
        else:
            # Use LLM for other languages
            test_results = await self._llm_based_testing(code, language, test_cases)
        
        results.update(test_results)
        
        # Generate summary using LLM
        results["summary"] = await self._generate_summary(results)
        
        return results
    
    async def _generate_test_cases(self, code: str, language: str) -> List[Dict]:
        """Use LLM to generate relevant test cases"""
        prompt = f"""You are a QA engineer. Generate comprehensive test cases for this {language} code.
        Include:
        1. Basic functionality tests
        2. Edge cases (empty input, negative values, etc.)
        3. Boundary tests
        4. Error handling tests
        
        Return as JSON array with format:
        [{{"input": "...", "expected": "...", "description": "..."}}]
        
        Code:
        {code}
        """
        
        messages = [
            SystemMessage(content="You are a test generation expert."),
            HumanMessage(content=prompt)
        ]
        
        response = await self.llm.ainvoke(messages)
        
        try:
            # Extract JSON from response
            import re
            json_match = re.search(r'\[.*\]', response.content, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
        except:
            logger.warning("Failed to parse generated tests")
            return []
        
        return []
    
    async def _run_python_tests(self, code: str, test_cases: List[Dict]) -> Dict:
        """Run Python code against test cases"""
        results = {
            "tests_passed": 0,
            "total_tests": len(test_cases),
            "test_results": [],
            "errors": []
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(code)
            f.write("\n\nif __name__ == '__main__':\n    pass\n")
            filename = f.name
        
        try:
            for test in test_cases:
                try:
                    # Create test script
                    test_script = f"""
import sys
import json
from {os.path.basename(filename).replace('.py', '')} import *

input_data = {json.dumps(test.get('input', ''))}
expected = {json.dumps(test.get('expected', ''))}

try:
    result = {test.get('function', 'main')}(input_data)
    print(json.dumps({{"passed": result == expected, "result": result}}))
except Exception as e:
    print(json.dumps({{"passed": False, "error": str(e)}}))
"""
                    
                    # Run test in subprocess
                    result = subprocess.run(
                        ['python', '-c', test_script],
                        capture_output=True,
                        text=True,
                        timeout=5
                    )
                    
                    if result.returncode == 0:
                        output = json.loads(result.stdout)
                        test_result = {
                            "name": test.get('description', 'Test'),
                            "passed": output.get('passed', False),
                            "input": test.get('input'),
                            "expected": test.get('expected'),
                            "actual": output.get('result')
                        }
                        
                        if output.get('passed'):
                            results["tests_passed"] += 1
                    else:
                        test_result = {
                            "name": test.get('description', 'Test'),
                            "passed": False,
                            "error": result.stderr
                        }
                    
                    results["test_results"].append(test_result)
                    
                except subprocess.TimeoutExpired:
                    results["test_results"].append({
                        "name": test.get('description', 'Test'),
                        "passed": False,
                        "error": "Test execution timed out"
                    })
                except Exception as e:
                    results["errors"].append(str(e))
                    
        finally:
            os.unlink(filename)
        
        return results
    
    async def _llm_based_testing(self, code: str, language: str, test_cases: List[Dict]) -> Dict:
        """Use LLM to simulate test execution for languages without direct execution"""
        results = {
            "tests_passed": 0,
            "total_tests": len(test_cases),
            "test_results": [],
            "errors": []
        }
        
        for test in test_cases:
            prompt = f"""Given this {language} code:
{code}

And this test case:
Input: {test.get('input')}
Expected: {test.get('expected')}
Description: {test.get('description')}

Analyze if the code would pass this test. Consider:
1. Does the code handle this input correctly?
2. Would there be any runtime errors?
3. Does the output match expected?

Respond with JSON: {{"passed": boolean, "actual": "predicted output", "reason": "explanation"}}
"""
            
            messages = [
                SystemMessage(content="You are a code execution simulator."),
                HumanMessage(content=prompt)
            ]
            
            response = await self.llm.ainvoke(messages)
            
            try:
                import re
                json_match = re.search(r'\{.*\}', response.content, re.DOTALL)
                if json_match:
                    result = json.loads(json_match.group())
                    test_result = {
                        "name": test.get('description', 'Test'),
                        "passed": result.get('passed', False),
                        "input": test.get('input'),
                        "expected": test.get('expected'),
                        "actual": result.get('actual'),
                        "reason": result.get('reason')
                    }
                    
                    if result.get('passed'):
                        results["tests_passed"] += 1
                    
                    results["test_results"].append(test_result)
            except:
                results["errors"].append(f"Failed to parse LLM response for test: {test.get('description')}")
        
        return results
    
    async def _generate_summary(self, results: Dict) -> str:
        """Generate human-readable summary of test results"""
        pass_rate = (results["tests_passed"] / results["total_tests"] * 100) if results["total_tests"] > 0 else 0
        
        prompt = f"""Summarize these test results in a helpful way:
        Tests Passed: {results['tests_passed']}/{results['total_tests']} ({pass_rate:.1f}%)
        
        Test Details:
        {json.dumps(results['test_results'], indent=2)}
        
        Provide:
        1. Overall assessment
        2. Patterns in failures
        3. Suggestions for fixing issues
        """
        
        messages = [
            SystemMessage(content="You are a helpful coding assistant summarizing test results."),
            HumanMessage(content=prompt)
        ]
        
        response = await self.llm.ainvoke(messages)
        return response.content