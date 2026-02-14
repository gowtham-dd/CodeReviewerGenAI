from langchain_core.messages import HumanMessage, SystemMessage
from langchain_groq import ChatGroq
import ast
import random
import string
from typing import Dict, List, Any
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EdgeCaseAgent:
    """
    Utility-Based Agent
    Generates and prioritizes edge cases for testing
    Weighs which cases are most likely to find bugs
    """
    
    def __init__(self, groq_api_key: str, model: str = "llama-3.1-8b-instant"):
        self.llm = ChatGroq(
            api_key=groq_api_key,
            model=model,
            temperature=0.4  # Higher temperature for creative edge cases
        )
    
    async def generate_cases(self, code: str, language: str, function_signature: str = None) -> Dict:
        """
        Generate comprehensive edge cases
        """
        logger.info(f"Generating edge cases for {language}")
        
        # Extract function signature if not provided
        if not function_signature and language == "python":
            function_signature = self._extract_python_signature(code)
        
        # Generate different types of edge cases
        edge_cases = {
            "boundary_cases": await self._generate_boundary_cases(code, language, function_signature),
            "invalid_inputs": await self._generate_invalid_inputs(code, language, function_signature),
            "stress_cases": await self._generate_stress_cases(code, language, function_signature),
            "integration_cases": await self._generate_integration_cases(code, language, function_signature),
            "priority_cases": []  # Will be filled with prioritized cases
        }
        
        # Prioritize cases
        edge_cases["priority_cases"] = await self._prioritize_cases(edge_cases)
        
        # Generate stress test if deep analysis enabled
        edge_cases["stress_test"] = await self._design_stress_test(code, language)
        
        return edge_cases
    
    def _extract_python_signature(self, code: str) -> str:
        """Extract main function signature from Python code"""
        try:
            tree = ast.parse(code)
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    # Get function name and arguments
                    args = []
                    for arg in node.args.args:
                        args.append(arg.arg)
                    
                    return {
                        "name": node.name,
                        "parameters": args,
                        "returns": self._get_return_annotation(node)
                    }
        except:
            pass
        return None
    
    def _get_return_annotation(self, node):
        """Extract return type annotation if present"""
        if node.returns:
            if isinstance(node.returns, ast.Name):
                return node.returns.id
        return "Any"
    
    async def _generate_boundary_cases(self, code: str, language: str, signature: Dict) -> List[Dict]:
        """Generate boundary value test cases"""
        prompt = f"""Generate boundary value test cases for this {language} code:

Code:
{code}

Function Signature: {signature}

Create test cases that test:
1. Minimum values
2. Maximum values
3. Empty/null values
4. Single element cases
5. Already sorted/processed cases

For each case, provide:
- name: descriptive name
- input: the test input
- expected: expected output (if known)
- severity: critical/high/medium/low
- description: why this case is important

Return as JSON array.
"""
        
        messages = [
            SystemMessage(content="You are a testing expert specializing in boundary value analysis."),
            HumanMessage(content=prompt)
        ]
        
        response = await self.llm.ainvoke(messages)
        return self._parse_cases(response.content)
    
    async def _generate_invalid_inputs(self, code: str, language: str, signature: Dict) -> List[Dict]:
        """Generate invalid input test cases"""
        prompt = f"""Generate invalid input test cases for this {language} code:

Code:
{code}

Function Signature: {signature}

Create test cases that test:
1. Wrong data types
2. Out of range values
3. Malformed data
4. None/Null inputs
5. Circular references
6. Unexpected characters

For each case, provide:
- name: descriptive name
- input: the test input
- expected_error: expected error type
- severity: critical/high/medium/low
- description: why this might break the code

Return as JSON array.
"""
        
        messages = [
            SystemMessage(content="You are a security testing expert."),
            HumanMessage(content=prompt)
        ]
        
        response = await self.llm.ainvoke(messages)
        return self._parse_cases(response.content)
    
    async def _generate_stress_cases(self, code: str, language: str, signature: Dict) -> List[Dict]:
        """Generate stress test cases"""
        prompt = f"""Generate stress test cases for this {language} code:

Code:
{code}

Function Signature: {signature}

Create test cases that test:
1. Very large inputs (1000x normal)
2. Repeated operations
3. Concurrent access patterns
4. Memory-intensive scenarios
5. Long-running operations

For each case, provide:
- name: descriptive name
- input_size: approximate size
- expected_behavior: what should happen
- severity: critical/high/medium/low
- description: performance implications

Return as JSON array.
"""
        
        messages = [
            SystemMessage(content="You are a performance testing expert."),
            HumanMessage(content=prompt)
        ]
        
        response = await self.llm.ainvoke(messages)
        return self._parse_cases(response.content)
    
    async def _generate_integration_cases(self, code: str, language: str, signature: Dict) -> List[Dict]:
        """Generate integration test cases"""
        prompt = f"""Generate integration test cases for this {language} code:

Code:
{code}

Function Signature: {signature}

Create test cases that test:
1. Function composition
2. State dependencies
3. Side effects
4. Resource cleanup
5. Exception propagation

For each case, provide:
- name: descriptive name
- scenario: the test scenario
- expected: expected outcome
- severity: critical/high/medium/low
- description: integration concerns

Return as JSON array.
"""
        
        messages = [
            SystemMessage(content="You are an integration testing expert."),
            HumanMessage(content=prompt)
        ]
        
        response = await self.llm.ainvoke(messages)
        return self._parse_cases(response.content)
    
    async def _prioritize_cases(self, all_cases: Dict) -> List[Dict]:
        """Prioritize test cases by importance"""
        all_tests = []
        for category, cases in all_cases.items():
            if isinstance(cases, list):
                for case in cases:
                    case["category"] = category
                    all_tests.append(case)
        
        # Sort by severity
        severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        all_tests.sort(key=lambda x: severity_order.get(x.get("severity", "medium"), 2))
        
        return all_tests[:10]  # Return top 10 priority cases
    
    async def _design_stress_test(self, code: str, language: str) -> Dict:
        """Design a comprehensive stress test"""
        prompt = f"""Design a stress test for this {language} code:

Code:
{code}

Provide a stress test plan including:
1. Maximum input size to test
2. Expected execution time
3. Memory usage estimates
4. Breaking point prediction
5. Performance bottlenecks

Return as JSON with keys: max_input, expected_time, memory_estimate, breaking_point, bottlenecks
"""
        
        messages = [
            SystemMessage(content="You are a stress testing expert."),
            HumanMessage(content=prompt)
        ]
        
        response = await self.llm.ainvoke(messages)
        
        import json
        import re
        
        try:
            json_match = re.search(r'\{.*\}', response.content, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
        except:
            pass
        
        return {
            "max_input": "Unknown",
            "expected_time": "Unknown",
            "memory_estimate": "Unknown",
            "breaking_point": "Unknown",
            "bottlenecks": ["Unable to analyze"]
        }
    
    def _parse_cases(self, response: str) -> List[Dict]:
        """Parse JSON response from LLM"""
        import json
        import re
        
        try:
            # Try to find JSON array in response
            json_match = re.search(r'\[.*\]', response, re.DOTALL)
            if json_match:
                cases = json.loads(json_match.group())
                return cases[:10]  # Limit to 10 cases per category
        except:
            logger.warning("Failed to parse edge cases")
        
        return []
    
    def generate_fuzzing_inputs(self, signature: Dict, count: int = 100) -> List[Any]:
        """Generate random fuzzing inputs"""
        fuzzed_inputs = []
        
        for _ in range(count):
            input_data = []
            for param in signature.get("parameters", []):
                # Generate random data based on parameter name hints
                if "list" in param.lower() or "array" in param.lower():
                    # Generate random list
                    size = random.randint(0, 10)
                    input_data.append([random.randint(-100, 100) for _ in range(size)])
                elif "str" in param.lower() or "string" in param.lower():
                    # Generate random string
                    length = random.randint(0, 20)
                    input_data.append(''.join(random.choices(string.ascii_letters, k=length)))
                elif "int" in param.lower() or "num" in param.lower():
                    # Generate random number
                    input_data.append(random.randint(-1000, 1000))
                else:
                    # Default to random value
                    input_data.append(random.choice([
                        None,
                        random.randint(-100, 100),
                        random.choice(string.ascii_letters),
                        [],
                        {}
                    ]))
            
            fuzzed_inputs.append(input_data[0] if len(input_data) == 1 else input_data)
        
        return fuzzed_inputs