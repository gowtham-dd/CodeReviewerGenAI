
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_groq import ChatGroq
import ast
import radon.complexity as radon_cc
from radon.raw import analyze
from radon.metrics import mi_visit, h_visit
from typing import Dict, List
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ComplexityAgent:
    """
    Model-Based + Utility Agent
    Analyzes time & space complexity using AST and static analysis
    Uses LLM for explanations and suggestions
    """
    
    def __init__(self, groq_api_key: str, model: str = "llama-3.1-8b-instant"):
        self.llm = ChatGroq(
            api_key=groq_api_key,
            model=model,
            temperature=0.2
        )
    
    async def analyze(self, code: str, language: str = "python") -> Dict:
        """
        Analyze code complexity
        """
        logger.info(f"Starting complexity analysis for {language}")
        
        if language == "python":
            analysis = await self._analyze_python(code)
        else:
            analysis = await self._analyze_general(code, language)
        
        # Get LLM explanation
        explanation = await self._generate_explanation(code, analysis)
        
        # Get optimization suggestions
        suggestions = await self._get_optimization_suggestions(code, analysis)
        
        return {
            "time_complexity": analysis.get("time", {}),
            "space_complexity": analysis.get("space", {}),
            "cyclomatic_complexity": analysis.get("cyclomatic", 0),
            "maintainability_index": analysis.get("maintainability", 0),
            "hotspots": analysis.get("hotspots", []),
            "explanation": explanation,
            "suggestions": suggestions
        }
    
    async def _analyze_python(self, code: str) -> Dict:
        """Deep analysis for Python code using AST and radon"""
        analysis = {
            "time": {"big_o": "O(1)", "explanation": "", "hotspots": []},
            "space": {"big_o": "O(1)", "explanation": "", "details": []},
            "cyclomatic": 0,
            "maintainability": 0,
            "hotspots": []
        }
        
        try:
            # Parse AST
            tree = ast.parse(code)
            
            # Analyze loops for time complexity
            loop_visitor = LoopComplexityVisitor()
            loop_visitor.visit(tree)
            analysis["time"] = loop_visitor.get_complexity()
            
            # Analyze memory allocations for space complexity
            memory_visitor = MemoryComplexityVisitor()
            memory_visitor.visit(tree)
            analysis["space"] = memory_visitor.get_complexity()
            
            # Calculate cyclomatic complexity using radon
            try:
                cc = radon_cc.cc_visit(code)
                if cc:
                    analysis["cyclomatic"] = max(c.complexity for c in cc)
                    analysis["hotspots"] = [
                        {"function": c.name, "complexity": c.complexity, "line": c.lineno}
                        for c in cc if c.complexity > 5
                    ]
            except:
                pass
            
            # Calculate maintainability index
            try:
                mi = mi_visit(code, multi=True)
                analysis["maintainability"] = mi
            except:
                pass
                
        except Exception as e:
            logger.error(f"Error in Python analysis: {e}")
        
        return analysis
    
    async def _analyze_general(self, code: str, language: str) -> Dict:
        """Use LLM for complexity analysis of other languages"""
        prompt = f"""Analyze the complexity of this {language} code:

{code}

Provide a detailed analysis including:
1. Time Complexity (Big O notation and explanation)
2. Space Complexity (Big O notation and explanation)
3. Identify specific lines/functions that contribute to complexity
4. Cyclomatic complexity estimate
5. Potential bottlenecks

Return as JSON with keys: time_complexity, space_complexity, hotspots, explanation
"""
        
        messages = [
            SystemMessage(content="You are a code complexity analysis expert."),
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
            "time": {"big_o": "Unknown", "explanation": response.content},
            "space": {"big_o": "Unknown", "explanation": ""},
            "hotspots": []
        }
    
    async def _generate_explanation(self, code: str, analysis: Dict) -> str:
        """Generate human-readable explanation of complexity"""
        prompt = f"""Explain the complexity of this code in simple terms:

Code:
{code}

Analysis:
Time Complexity: {analysis.get('time', {}).get('big_o', 'Unknown')}
Space Complexity: {analysis.get('space', {}).get('big_o', 'Unknown')}
Cyclomatic Complexity: {analysis.get('cyclomatic', 0)}

Provide an explanation that:
1. Is easy to understand for beginners
2. Points out specific lines causing complexity
3. Explains the real-world impact
"""
        
        messages = [
            SystemMessage(content="You are a patient coding teacher explaining complexity."),
            HumanMessage(content=prompt)
        ]
        
        response = await self.llm.ainvoke(messages)
        return response.content
    
    async def _get_optimization_suggestions(self, code: str, analysis: Dict) -> List[str]:
        """Get suggestions for optimizing code"""
        prompt = f"""Suggest specific optimizations for this code:

{code}

Current Complexity:
Time: {analysis.get('time', {}).get('big_o', 'Unknown')}
Space: {analysis.get('space', {}).get('big_o', 'Unknown')}

Provide 3-5 specific, actionable suggestions to improve performance.
Focus on the most impactful changes first.
"""
        
        messages = [
            SystemMessage(content="You are a performance optimization expert."),
            HumanMessage(content=prompt)
        ]
        
        response = await self.llm.ainvoke(messages)
        return [s.strip() for s in response.content.split('\n') if s.strip()]


class LoopComplexityVisitor(ast.NodeVisitor):
    """AST visitor to detect loop complexity patterns"""
    
    def __init__(self):
        self.loop_depth = 0
        self.max_depth = 0
        self.loop_lines = []
        self.complexity_factors = []
    
    def visit_For(self, node):
        self.loop_depth += 1
        self.max_depth = max(self.max_depth, self.loop_depth)
        self.loop_lines.append(node.lineno)
        
        # Check for nested loops
        if self.loop_depth > 1:
            self.complexity_factors.append(f"nested loop starting line {node.lineno}")
        
        self.generic_visit(node)
        self.loop_depth -= 1
    
    def visit_While(self, node):
        self.loop_depth += 1
        self.max_depth = max(self.max_depth, self.loop_depth)
        self.loop_lines.append(node.lineno)
        
        if self.loop_depth > 1:
            self.complexity_factors.append(f"nested while loop starting line {node.lineno}")
        
        self.generic_visit(node)
        self.loop_depth -= 1
    
    def get_complexity(self):
        """Determine Big O based on loop depth"""
        if self.max_depth == 0:
            big_o = "O(1)"
            explanation = "No loops detected - constant time"
        elif self.max_depth == 1:
            big_o = "O(n)"
            explanation = "Single loop - linear time"
        elif self.max_depth == 2:
            big_o = "O(n²)"
            explanation = "Nested loops detected - quadratic time"
        else:
            big_o = f"O(n^{self.max_depth})"
            explanation = f"Deeply nested loops (depth {self.max_depth}) - polynomial time"
        
        return {
            "big_o": big_o,
            "explanation": explanation,
            "hotspots": self.complexity_factors
        }


class MemoryComplexityVisitor(ast.NodeVisitor):
    """AST visitor to detect memory allocation patterns"""
    
    def __init__(self):
        self.allocations = []
        self.current_function = None
    
    def visit_FunctionDef(self, node):
        self.current_function = node.name
        self.generic_visit(node)
    
    def visit_List(self, node):
        if hasattr(node, 'ctx') and isinstance(node.ctx, ast.Store):
            self.allocations.append(f"List allocation in {self.current_function} at line {node.lineno}")
        self.generic_visit(node)
    
    def visit_Dict(self, node):
        if hasattr(node, 'ctx') and isinstance(node.ctx, ast.Store):
            self.allocations.append(f"Dict allocation in {self.current_function} at line {node.lineno}")
        self.generic_visit(node)
    
    def visit_Call(self, node):
        # Check for list/dict comprehensions and constructors
        if isinstance(node.func, ast.Name):
            if node.func.id in ['list', 'dict', 'set']:
                self.allocations.append(f"Collection constructor in {self.current_function} at line {node.lineno}")
        self.generic_visit(node)
    
    def get_complexity(self):
        """Estimate space complexity based on allocations"""
        if not self.allocations:
            big_o = "O(1)"
            explanation = "Constant space usage"
        else:
            big_o = "O(n)"
            explanation = f"Allocates data structures based on input size"
        
        return {
            "big_o": big_o,
            "explanation": explanation,
            "details": self.allocations[:5]  # Limit to top 5
        }