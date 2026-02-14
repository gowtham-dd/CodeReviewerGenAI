from langchain_core.messages import HumanMessage, SystemMessage
from langchain_groq import ChatGroq
import ast
import pylint.lint
from pylint.reporters import JSONReporter
import io
import black
from typing import Dict, List
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ReadabilityAgent:
    """
    Goal-Based + Learning Agent
    Goal: Ensure code follows best practices and is readable
    Learns from user feedback to adapt suggestions
    """
    
    def __init__(self, groq_api_key: str, model: str = "llama-3.1-8b-instant"):
        self.llm = ChatGroq(
            api_key=groq_api_key,
            model=model,
            temperature=0.3
        )
        self.user_preferences = {}  # Store user style preferences
    
    async def review(self, code: str, language: str, user_id: str = None) -> Dict:
        """
        Review code readability and best practices
        """
        logger.info(f"Starting readability review for {language}")
        
        # Get user preferences if available
        preferences = self.user_preferences.get(user_id, {}) if user_id else {}
        
        if language == "python":
            analysis = await self._analyze_python(code, preferences)
        else:
            analysis = await self._analyze_general(code, language, preferences)
        
        # Get improvement suggestions
        suggestions = await self._generate_suggestions(code, language, analysis)
        
        # Try to format code if possible
        formatted_code = await self._format_code(code, language)
        
        return {
            **analysis,
            "suggestions": suggestions,
            "formatted_code": formatted_code
        }
    
    async def _analyze_python(self, code: str, preferences: Dict) -> Dict:
        """Deep Python-specific readability analysis"""
        analysis = {
            "scores": {
                "style": 0,
                "documentation": 0,
                "naming": 0,
                "structure": 0
            },
            "issues": [],
            "metrics": {}
        }
        
        try:
            # Parse AST for structural analysis
            tree = ast.parse(code)
            
            # Check naming conventions
            naming_visitor = NamingConventionVisitor()
            naming_visitor.visit(tree)
            analysis["scores"]["naming"] = naming_visitor.score
            analysis["issues"].extend(naming_visitor.issues)
            
            # Check documentation
            doc_visitor = DocumentationVisitor()
            doc_visitor.visit(tree)
            analysis["scores"]["documentation"] = doc_visitor.score
            analysis["issues"].extend(doc_visitor.issues)
            
            # Check structure (function length, complexity)
            struct_visitor = StructureVisitor()
            struct_visitor.visit(tree)
            analysis["scores"]["structure"] = struct_visitor.score
            analysis["issues"].extend(struct_visitor.issues)
            
            # Run pylint for additional checks
            pylint_results = self._run_pylint(code)
            if pylint_results:
                analysis["issues"].extend(pylint_results)
            
            # Calculate overall style score
            analysis["scores"]["style"] = self._calculate_style_score(analysis["issues"])
            
            # Add metrics
            analysis["metrics"] = {
                "lines": len(code.splitlines()),
                "functions": naming_visitor.function_count,
                "classes": naming_visitor.class_count,
                "avg_function_length": struct_visitor.avg_function_length
            }
            
        except Exception as e:
            logger.error(f"Error in Python readability analysis: {e}")
            analysis["issues"].append(f"Parse error: {str(e)}")
        
        return analysis
    
    def _run_pylint(self, code: str) -> List[str]:
        """Run pylint on code and collect issues"""
        issues = []
        
        try:
            # Create a temporary file
            import tempfile
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
                f.write(code)
                filename = f.name
            
            # Run pylint
            pylint_output = io.StringIO()
            reporter = JSONReporter(pylint_output)
            pylint.lint.Run([filename], reporter=reporter, exit=False)
            
            # Parse results
            import json
            results = json.loads(pylint_output.getvalue())
            
            for result in results:
                if result['type'] in ['convention', 'refactor', 'warning']:
                    issues.append(f"Line {result['line']}: {result['message']}")
            
            # Clean up
            import os
            os.unlink(filename)
            
        except Exception as e:
            logger.error(f"Pylint error: {e}")
        
        return issues[:10]  # Limit to top 10 issues
    
    async def _analyze_general(self, code: str, language: str, preferences: Dict) -> Dict:
        """Use LLM for readability analysis of other languages"""
        prompt = f"""Analyze the readability and best practices of this {language} code:

{code}

Provide a detailed analysis including:
1. Naming conventions (score 0-10)
2. Documentation/comments (score 0-10)
3. Code structure/organization (score 0-10)
4. Best practices adherence (score 0-10)
5. List specific issues with line numbers
6. Suggestions for improvement

User preferences: {preferences.get('style', 'standard')}

Return as JSON with keys: scores (object with style, documentation, naming, structure), issues (array), suggestions (array)
"""
        
        messages = [
            SystemMessage(content="You are a code review expert focused on readability."),
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
            "scores": {"style": 5, "documentation": 5, "naming": 5, "structure": 5},
            "issues": ["Analysis limited - using general guidelines"],
            "suggestions": []
        }
    
    async def _generate_suggestions(self, code: str, language: str, analysis: Dict) -> List[str]:
        """Generate actionable improvement suggestions"""
        prompt = f"""Based on this readability analysis, provide specific, actionable suggestions to improve the code:

Code:
{code}

Analysis:
Scores: {analysis.get('scores', {})}
Issues: {analysis.get('issues', [])}

Provide 3-5 concrete suggestions that:
1. Are specific and actionable
2. Include code examples where helpful
3. Prioritize the most important issues first
"""
        
        messages = [
            SystemMessage(content="You are a code quality expert."),
            HumanMessage(content=prompt)
        ]
        
        response = await self.llm.ainvoke(messages)
        return [s.strip() for s in response.content.split('\n') if s.strip()]
    
    async def _format_code(self, code: str, language: str) -> str:
        """Attempt to format code according to language standards"""
        if language == "python":
            try:
                return black.format_str(code, mode=black.Mode())
            except:
                return code
        elif language == "javascript":
            # Could integrate prettier here
            return code
        else:
            return code
    
    def _calculate_style_score(self, issues: List[str]) -> int:
        """Calculate style score based on issues count"""
        base_score = 10
        penalty = min(len(issues), 10)  # Max penalty of 10 points
        return max(0, base_score - penalty)


class NamingConventionVisitor(ast.NodeVisitor):
    """Check naming conventions"""
    
    def __init__(self):
        self.issues = []
        self.score = 10
        self.function_count = 0
        self.class_count = 0
    
    def visit_FunctionDef(self, node):
        self.function_count += 1
        # Check snake_case for functions
        if not node.name.islower() or '_' not in node.name:
            self.issues.append(f"Line {node.lineno}: Function '{node.name}' should use snake_case")
            self.score -= 1
        self.generic_visit(node)
    
    def visit_ClassDef(self, node):
        self.class_count += 1
        # Check CamelCase for classes
        if not node.name[0].isupper():
            self.issues.append(f"Line {node.lineno}: Class '{node.name}' should use CamelCase")
            self.score -= 1
        self.generic_visit(node)
    
    def visit_Name(self, node):
        if isinstance(node.ctx, ast.Store):
            # Check variable naming
            if len(node.id) == 1 and node.id not in ['i', 'j', 'k', 'x', 'y']:
                self.issues.append(f"Line {node.lineno}: Variable '{node.id}' - consider a more descriptive name")
                self.score -= 0.5
        self.generic_visit(node)


class DocumentationVisitor(ast.NodeVisitor):
    """Check documentation and comments"""
    
    def __init__(self):
        self.issues = []
        self.score = 10
        self.functions_with_docstring = 0
        self.total_functions = 0
    
    def visit_FunctionDef(self, node):
        self.total_functions += 1
        if not ast.get_docstring(node):
            self.issues.append(f"Line {node.lineno}: Function '{node.name}' missing docstring")
            self.score -= 1
        else:
            self.functions_with_docstring += 1
        self.generic_visit(node)
    
    def visit_ClassDef(self, node):
        if not ast.get_docstring(node):
            self.issues.append(f"Line {node.lineno}: Class '{node.name}' missing docstring")
            self.score -= 1
        self.generic_visit(node)
    
    def visit_Module(self, node):
        if not ast.get_docstring(node):
            self.issues.append("Module missing docstring")
            self.score -= 1
        self.generic_visit(node)


class StructureVisitor(ast.NodeVisitor):
    """Check code structure"""
    
    def __init__(self):
        self.issues = []
        self.score = 10
        self.function_lengths = []
        self.avg_function_length = 0
    
    def visit_FunctionDef(self, node):
        # Check function length
        function_lines = node.end_lineno - node.lineno if hasattr(node, 'end_lineno') else 0
        self.function_lengths.append(function_lines)
        
        if function_lines > 50:
            self.issues.append(f"Line {node.lineno}: Function '{node.name}' is too long ({function_lines} lines)")
            self.score -= 1
        elif function_lines > 30:
            self.issues.append(f"Line {node.lineno}: Consider breaking down function '{node.name}'")
            self.score -= 0.5
        
        # Check number of arguments
        if len(node.args.args) > 5:
            self.issues.append(f"Line {node.lineno}: Function '{node.name}' has too many arguments ({len(node.args.args)})")
            self.score -= 1
        
        self.generic_visit(node)
    
    def visit_Module(self, node):
        # Calculate average function length
        if self.function_lengths:
            self.avg_function_length = sum(self.function_lengths) / len(self.function_lengths)
        self.generic_visit(node)