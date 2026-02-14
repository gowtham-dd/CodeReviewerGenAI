from langchain_core.messages import HumanMessage, SystemMessage
from langchain_groq import ChatGroq
from typing import Dict, List
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SummarizerAgent:
    """
    Learning + Utility Agent
    Synthesizes all agent reports into cohesive feedback
    Learns from user ratings to improve summaries
    """
    
    def __init__(self, groq_api_key: str, model: str = "llama-3.1-8b-instant"):
        self.llm = ChatGroq(
            api_key=groq_api_key,
            model=model,
            temperature=0.3
        )
        self.feedback_history = []
    
    async def summarize(self, 
                       code: str,
                       language: str,
                       correctness_report: Dict,
                       complexity_report: Dict,
                       readability_report: Dict,
                       edge_cases_report: Dict,
                       user_id: str = None) -> Dict:
        """
        Summarize all agent reports into a comprehensive review
        """
        logger.info("Starting summary generation")
        
        # Calculate overall score
        overall_score = self._calculate_overall_score([
            correctness_report,
            complexity_report,
            readability_report,
            edge_cases_report
        ])
        
        # Identify critical issues
        critical_issues = self._identify_critical_issues([
            correctness_report,
            complexity_report,
            readability_report,
            edge_cases_report
        ])
        
        # Generate executive summary
        executive_summary = await self._generate_executive_summary(
            code, language, overall_score, critical_issues
        )
        
        # Generate improvement recommendations
        improvements = await self._generate_improvements(
            code, language, [
                correctness_report,
                complexity_report,
                readability_report,
                edge_cases_report
            ]
        )
        
        # Generate optimized code if possible
        optimized_code = await self._generate_optimized_code(code, language, improvements)
        
        # Get user preferences if available
        user_preferences = self._get_user_preferences(user_id) if user_id else {}
        
        # Adapt summary based on user preferences
        if user_preferences.get('style') == 'concise':
            executive_summary = self._make_concise(executive_summary)
        elif user_preferences.get('style') == 'detailed':
            executive_summary = self._make_detailed(executive_summary)
        
        return {
            "overall_score": overall_score,
            "critical_issues": critical_issues,
            "executive_summary": executive_summary,
            "improvements": improvements,
            "optimized_code": optimized_code,
            "agent_scores": {
                "correctness": correctness_report.get("tests_passed", 0) / max(correctness_report.get("total_tests", 1), 1) * 100 if correctness_report.get("total_tests") else 0,
                "complexity": self._score_complexity(complexity_report),
                "readability": sum(readability_report.get("scores", {}).values()) / 4 * 10 if readability_report.get("scores") else 0,
                "robustness": len(edge_cases_report.get("priority_cases", [])) / 10 * 100 if edge_cases_report.get("priority_cases") else 50
            }
        }
    
    def _calculate_overall_score(self, reports: List[Dict]) -> int:
        """Calculate weighted overall score"""
        weights = {
            "correctness": 0.35,  # Most important
            "complexity": 0.25,
            "readability": 0.20,
            "robustness": 0.20
        }
        
        scores = {
            "correctness": reports[0].get("tests_passed", 0) / max(reports[0].get("total_tests", 1), 1) * 100 if reports[0].get("total_tests") else 70,
            "complexity": self._score_complexity(reports[1]),
            "readability": sum(reports[2].get("scores", {}).values()) / 4 * 10 if reports[2].get("scores") else 70,
            "robustness": len(reports[3].get("priority_cases", [])) / 10 * 100 if reports[3].get("priority_cases") else 70
        }
        
        total = sum(scores[key] * weights[key] for key in weights)
        return int(total)
    
    def _score_complexity(self, complexity_report: Dict) -> float:
        """Convert complexity analysis to score"""
        time_complexity = complexity_report.get("time_complexity", {}).get("big_o", "O(n)")
        
        # Simple scoring based on Big O
        complexity_scores = {
            "O(1)": 100,
            "O(log n)": 90,
            "O(n)": 80,
            "O(n log n)": 70,
            "O(n²)": 50,
            "O(n³)": 30,
            "O(2^n)": 10
        }
        
        for pattern, score in complexity_scores.items():
            if pattern in time_complexity:
                return score
        
        return 60  # Default score
    
    def _identify_critical_issues(self, reports: List[Dict]) -> List[str]:
        """Extract critical issues from all reports"""
        critical_issues = []
        
        # Check correctness for failing tests
        if reports[0].get("total_tests", 0) > 0:
            failed = reports[0]["total_tests"] - reports[0]["tests_passed"]
            if failed > 0:
                critical_issues.append(f"{failed} test(s) failing")
        
        # Check complexity hotspots
        hotspots = reports[1].get("hotspots", [])
        if hotspots:
            critical_issues.append(f"High complexity in: {', '.join([h.get('function', 'unknown') for h in hotspots[:3]])}")
        
        # Check readability issues
        readability_issues = reports[2].get("issues", [])
        if len(readability_issues) > 5:
            critical_issues.append(f"{len(readability_issues)} readability issues found")
        
        # Check critical edge cases
        priority_cases = reports[3].get("priority_cases", [])
        critical_cases = [c for c in priority_cases if c.get("severity") == "critical"]
        if critical_cases:
            critical_issues.append(f"{len(critical_cases)} critical edge cases to test")
        
        return critical_issues[:5]  # Limit to top 5
    
    async def _generate_executive_summary(self, code: str, language: str, score: int, issues: List[str]) -> str:
        """Generate executive summary"""
        prompt = f"""Write an executive summary for this code review:

Language: {language}
Overall Score: {score}/100
Critical Issues: {', '.join(issues) if issues else 'None'}

Code:
{code[:500]}... (truncated)

Provide a concise, professional summary that:
1. Gives an overall assessment
2. Highlights strengths
3. Points out main areas for improvement
4. Provides actionable next steps

Keep it to 3-4 paragraphs.
"""
        
        messages = [
            SystemMessage(content="You are a tech lead writing a code review summary."),
            HumanMessage(content=prompt)
        ]
        
        response = await self.llm.ainvoke(messages)
        return response.content
    
    async def _generate_improvements(self, code: str, language: str, reports: List[Dict]) -> List[Dict]:
        """Generate prioritized improvement recommendations"""
        # Collect all suggestions
        all_suggestions = []
        
        # From correctness agent
        if "summary" in reports[0]:
            all_suggestions.append({
                "title": "Fix Failing Tests",
                "description": reports[0]["summary"],
                "priority": "high"
            })
        
        # From complexity agent
        for suggestion in reports[1].get("suggestions", []):
            all_suggestions.append({
                "title": "Performance Optimization",
                "description": suggestion,
                "priority": "medium"
            })
        
        # From readability agent
        for suggestion in reports[2].get("suggestions", []):
            all_suggestions.append({
                "title": "Code Quality Improvement",
                "description": suggestion,
                "priority": "medium"
            })
        
        # Use LLM to prioritize and format
        prompt = f"""Prioritize and format these improvement suggestions:

Suggestions:
{all_suggestions}

Return a list of 3-5 most important improvements, each with:
- title: short descriptive title
- description: detailed explanation
- priority: high/medium/low
- effort: small/medium/large
- impact: high/medium/low

Return as JSON array.
"""
        
        messages = [
            SystemMessage(content="You are a project manager prioritizing technical improvements."),
            HumanMessage(content=prompt)
        ]
        
        response = await self.llm.ainvoke(messages)
        
        import json
        import re
        
        try:
            json_match = re.search(r'\[.*\]', response.content, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
        except:
            pass
        
        return all_suggestions[:5]
    
    async def _generate_optimized_code(self, code: str, language: str, improvements: List[Dict]) -> str:
        """Attempt to generate optimized version of code"""
        prompt = f"""Based on these improvements, provide an optimized version of this {language} code:

Original Code:
{code}

Improvements to incorporate:
{improvements}

Return the optimized code with comments explaining the key changes.
"""
        
        messages = [
            SystemMessage(content="You are an expert programmer writing optimized code."),
            HumanMessage(content=prompt)
        ]
        
        response = await self.llm.ainvoke(messages)
        return response.content
    
    def _make_concise(self, summary: str) -> str:
        """Make summary more concise"""
        # Could use LLM to shorten, but for now just return first paragraph
        paragraphs = summary.split('\n\n')
        return paragraphs[0] if paragraphs else summary
    
    def _make_detailed(self, summary: str) -> str:
        """Make summary more detailed"""
        # Add note about detail level
        return summary + "\n\n*This is a detailed summary. For a shorter version, adjust your preferences.*"
    
    def _get_user_preferences(self, user_id: str) -> Dict:
        """Get user preferences from history"""
        # Filter feedback for this user
        user_feedback = [f for f in self.feedback_history if f.get("user_id") == user_id]
        
        if not user_feedback:
            return {}
        
        # Determine preferred style
        concise_count = sum(1 for f in user_feedback if f.get("rating", 3) < 3)
        detailed_count = sum(1 for f in user_feedback if f.get("rating", 3) > 3)
        
        if concise_count > detailed_count:
            return {"style": "concise"}
        elif detailed_count > concise_count:
            return {"style": "detailed"}
        else:
            return {}
    
    def record_feedback(self, review_id: str, user_id: str, rating: int, comments: str = ""):
        """Record user feedback for learning"""
        self.feedback_history.append({
            "review_id": review_id,
            "user_id": user_id,
            "rating": rating,
            "comments": comments,
            "timestamp": import_datetime().datetime.now().isoformat()
        })
    
    def import_datetime(self):
        """Helper to import datetime"""
        from datetime import datetime
        return datetime