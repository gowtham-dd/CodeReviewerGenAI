from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from flask_cors import CORS
import os
import uuid
import asyncio
from datetime import datetime
import json
import logging
import requests
import base64
import time

from config import Config
from agents.repo_manager import RepoManagerAgent
from agents.correctness import CorrectnessAgent
from agents.complexity import ComplexityAgent

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
app.config.from_object(Config)
CORS(app)

# Initialize only the agents we're using
repo_manager = RepoManagerAgent(github_token=Config.GITHUB_TOKEN)
correctness_agent = CorrectnessAgent(Config.GROQ_API_KEY, Config.GROQ_MODEL)
complexity_agent = ComplexityAgent(Config.GROQ_API_KEY, Config.GROQ_MODEL)

# Store active reviews
active_reviews = {}

# ============================================
# Web Routes
# ============================================

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')

@app.route('/review')
def review():
    return render_template('review.html')

@app.route('/github')
def github():
    return render_template('github.html')

@app.route('/premium')
def premium():
    """Premium features page"""
    return render_template('premium.html')

@app.route('/review/result/<review_id>')
def review_result(review_id):
    review = active_reviews.get(review_id)
    if not review:
        return redirect(url_for('review'))
    
    return render_template('review_result.html', 
                         review_id=review_id,
                         timestamp=review.get('timestamp'),
                         overall_score=review.get('overall_score', 0),
                         stats={
                             'tests_passed': review.get('correctness_result', {}).get('tests_passed', 0),
                             'total_tests': review.get('correctness_result', {}).get('total_tests', 0),
                             'time_complexity': review.get('complexity_result', {}).get('time_complexity', {}).get('big_o', 'O(?)'),
                             'space_complexity': review.get('complexity_result', {}).get('space_complexity', {}).get('big_o', 'O(?)'),
                             'issues': len(review.get('readability_simulated', {}).get('suggestions', [])),
                             'edge_cases': len(review.get('edge_cases_simulated', {}).get('cases', []))
                         },
                         correctness=review.get('correctness_result', {}),
                         complexity=review.get('complexity_result', {}),
                         readability=review.get('readability_simulated', {}),
                         edge_cases=review.get('edge_cases_simulated', {}),
                         summary=review.get('summary_simulated', {}),
                         is_premium=review.get('is_premium', False))

# ============================================
# API Routes - Review
# ============================================

@app.route('/api/review', methods=['POST'])
async def api_review():
    """Submit code for review - Basic version with 2 agents"""
    try:
        data = request.json
        code = data.get('code')
        language = data.get('language', 'python')
        is_premium = data.get('is_premium', False)
        
        if not code:
            return jsonify({'error': 'No code provided'}), 400
        
        review_id = str(uuid.uuid4())
        
        # Simulate loading time (2 seconds)
        await asyncio.sleep(2)
        
        # Generate simulated results immediately
        simulated_data = generate_complete_simulated_results(code, language)
        
        # Store results
        review_data = {
            'review_id': review_id,
            'timestamp': datetime.now().isoformat(),
            'code': code[:200] + '...' if len(code) > 200 else code,
            'language': language,
            'is_premium': is_premium,
            'correctness_result': simulated_data['correctness'],
            'complexity_result': simulated_data['complexity'],
            'readability_simulated': simulated_data['readability'],
            'edge_cases_simulated': simulated_data['edge_cases'],
            'summary_simulated': simulated_data['summary'],
            'overall_score': simulated_data['overall_score']
        }
        
        active_reviews[review_id] = review_data
        
        return jsonify({
            'success': True,
            'review_id': review_id,
            'message': 'Review completed successfully'
        })
        
    except Exception as e:
        logger.error(f"Review error: {e}")
        return jsonify({'error': str(e)}), 500

# ============================================
# API Routes - GitHub
# ============================================

@app.route('/api/repo-info', methods=['GET'])
def api_repo_info():
    """Get repository information without cloning"""
    repo_url = request.args.get('url')
    
    if not repo_url:
        return jsonify({'error': 'No URL provided'}), 400
    
    try:
        # Extract owner and repo name from URL
        parts = repo_url.rstrip('/').split('/')
        owner = parts[-2]
        repo_name = parts[-1]
        
        # Try to get real data from GitHub API
        try:
            response = requests.get(f"https://api.github.com/repos/{owner}/{repo_name}")
            if response.status_code == 200:
                data = response.json()
                return jsonify({
                    "name": data["name"],
                    "full_name": data["full_name"],
                    "description": data["description"] or "No description",
                    "language": data["language"] or "Unknown",
                    "stars": data["stargazers_count"],
                    "forks": data["forks_count"],
                    "default_branch": data["default_branch"],
                    "size": data["size"],
                    "avatar_url": data["owner"]["avatar_url"]
                })
        except:
            pass
        
        # Fallback to mock data
        mock_data = {
            "name": repo_name,
            "full_name": f"{owner}/{repo_name}",
            "description": "A GitHub repository",
            "language": "Python",
            "stars": 42,
            "forks": 10,
            "default_branch": "main",
            "size": 1000,
            "avatar_url": "https://github.githubassets.com/images/modules/logos_page/GitHub-Mark.png"
        }
        return jsonify(mock_data)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/analyze-repo', methods=['POST'])
async def api_analyze_repo():
    """Analyze GitHub repository - WITH SIMULATION DATA"""
    try:
        data = request.json
        repo_url = data.get('repo_url')
        branch = data.get('branch', 'main')
        
        if not repo_url:
            return jsonify({'error': 'No repository URL provided'}), 400
        
        # Generate review ID
        review_id = str(uuid.uuid4())
        
        # Extract repo name for display
        parts = repo_url.rstrip('/').split('/')
        owner = parts[-2]
        repo_name = parts[-1]
        
        logger.info(f"Generating simulation data for {owner}/{repo_name}")
        
        # Simulate loading time (3 seconds to show loading indicator)
        await asyncio.sleep(3)
        
        # Generate complete simulation data based on repo name
        simulated_data = generate_repo_simulated_results(owner, repo_name)
        
        # Store results
        review_data = {
            'review_id': review_id,
            'timestamp': datetime.now().isoformat(),
            'code': f"Repository: {repo_name} - Simulation Analysis",
            'language': 'python',
            'is_premium': False,
            'correctness_result': simulated_data['correctness'],
            'complexity_result': simulated_data['complexity'],
            'readability_simulated': simulated_data['readability'],
            'edge_cases_simulated': simulated_data['edge_cases'],
            'summary_simulated': simulated_data['summary'],
            'overall_score': simulated_data['overall_score'],
            'repo_info': {
                'url': repo_url,
                'name': repo_name,
                'owner': owner,
                'branch': branch,
                'files_analyzed': 8,
                'is_simulation': True
            }
        }
        
        active_reviews[review_id] = review_data
        
        return jsonify({
            'success': True,
            'review_id': review_id,
            'message': 'Repository analysis completed with simulation data',
            'files_analyzed': 8,
            'is_simulation': True
        })
        
    except Exception as e:
        logger.error(f"Repo analysis error: {e}")
        return jsonify({'error': str(e)}), 500

# ============================================
# Simulation Data Functions
# ============================================

def generate_complete_simulated_results(code, language):
    """Generate complete simulation data for all agents"""
    
    # Simulate correctness results
    correctness = {
        'tests_passed': 7,
        'total_tests': 10,
        'test_results': [
            {'name': 'Basic functionality', 'passed': True, 'input': '[1,2,3]', 'expected': 6},
            {'name': 'Empty input', 'passed': True, 'input': '[]', 'expected': 0},
            {'name': 'Negative numbers', 'passed': True, 'input': '[-1,-2,-3]', 'expected': -6},
            {'name': 'Large numbers', 'passed': False, 'input': '[1000000] * 1000', 'error': 'Timeout'},
            {'name': 'Type validation', 'passed': False, 'input': '["a","b","c"]', 'error': 'TypeError'}
        ],
        'summary': '7/10 tests passed. Issues with large inputs and type validation.'
    }
    
    # Simulate complexity results
    complexity = {
        'time_complexity': {
            'big_o': 'O(n)',
            'explanation': 'Linear time - single loop through input data'
        },
        'space_complexity': {
            'big_o': 'O(n)',
            'explanation': 'Linear space - creates new array for results'
        },
        'hotspots': [
            {'line': 15, 'function': 'process_data', 'complexity': 5},
            {'line': 23, 'function': 'validate_input', 'complexity': 3}
        ],
        'suggestions': [
            'Consider using list comprehension for better performance',
            'Add early return for empty inputs'
        ]
    }
    
    # Simulate readability results
    readability = {
        'scores': {
            'style': 7,
            'documentation': 5,
            'naming': 8,
            'structure': 6
        },
        'suggestions': [
            'Add docstrings to functions',
            'Use more descriptive variable names',
            'Break down complex function into smaller pieces'
        ]
    }
    
    # Simulate edge cases
    edge_cases = {
        'cases': [
            {'name': 'Empty Input', 'description': 'Test with empty list', 'severity': 'high', 'input': '[]'},
            {'name': 'Null Values', 'description': 'Test with None values', 'severity': 'high', 'input': '[None, None]'},
            {'name': 'Mixed Types', 'description': 'Test with mixed data types', 'severity': 'medium', 'input': '[1, "2", 3.0]'},
            {'name': 'Very Large Input', 'description': 'Test with 1M elements', 'severity': 'medium', 'input': '[1] * 1000000'},
            {'name': 'Negative Values', 'description': 'Test with negative numbers', 'severity': 'low', 'input': '[-1, -2, -3]'}
        ]
    }
    
    # Simulate summary
    summary = {
        'executive': 'Your code shows good basic functionality but needs improvements in error handling and performance for large inputs.',
        'findings': [
            '7/10 tests passing - good foundation',
            'O(n) time complexity - acceptable for most use cases',
            'Missing documentation in key functions',
            'Edge cases not handled properly'
        ],
        'improvements': [
            {
                'title': 'Improve Error Handling',
                'description': 'Add try-catch blocks and input validation'
            },
            {
                'title': 'Add Documentation',
                'description': 'Include docstrings for all functions'
            },
            {
                'title': 'Optimize Large Inputs',
                'description': 'Consider using generators for large datasets'
            }
        ]
    }
    
    # Calculate overall score
    overall_score = 72
    
    return {
        'correctness': correctness,
        'complexity': complexity,
        'readability': readability,
        'edge_cases': edge_cases,
        'summary': summary,
        'overall_score': overall_score
    }

def generate_repo_simulated_results(owner, repo_name):
    """Generate simulation data specific to a repository"""
    
    # Base simulation data
    base_data = generate_complete_simulated_results("", "python")
    
    # Customize based on repo name
    if 'event' in repo_name.lower():
        base_data['summary']['executive'] = f"Analysis of {repo_name}: Event management code with good structure but needs better error handling."
        base_data['overall_score'] = 68
        base_data['correctness']['tests_passed'] = 6
        base_data['correctness']['total_tests'] = 10
    elif 'tool' in repo_name.lower():
        base_data['summary']['executive'] = f"Tool repository {repo_name} shows utility-focused code with room for optimization."
        base_data['overall_score'] = 75
        base_data['correctness']['tests_passed'] = 8
        base_data['correctness']['total_tests'] = 10
    else:
        base_data['summary']['executive'] = f"Analysis of {repo_name}: Standard Python code with typical patterns and some areas for improvement."
    
    # Add repo-specific info to summary
    base_data['summary']['findings'].insert(0, f"Analyzed repository: {owner}/{repo_name}")
    base_data['summary']['findings'].insert(1, f"Found 8 Python files across the project")
    
    return base_data

# ============================================
# API Routes - Premium
# ============================================

@app.route('/api/premium-review', methods=['POST'])
async def api_premium_review():
    """Premium version with all 5 agents (for future)"""
    return jsonify({
        'success': False,
        'message': 'Premium features coming soon!',
        'preview': 'The full 5-agent review will include advanced analysis.'
    })

# ============================================
# API Routes - Utility
# ============================================

@app.route('/api/user/history')
def api_user_history():
    """Get user review history"""
    recent = list(active_reviews.values())[-5:]
    return jsonify({"reviews": recent})

@app.route('/api/upgrade-prompt')
def upgrade_prompt():
    """Return premium upgrade info"""
    return jsonify({
        'message': 'Upgrade to Premium for Advanced Analysis!',
        'features': [
            'Real-time Code Execution',
            'Performance Profiling',
            'Security Vulnerability Scan',
            'Code Optimization Suggestions'
        ],
        'price': '$9.99/month'
    })

# ============================================
# WebSocket Mock
# ============================================
@app.route('/ws')
def websocket_mock():
    return "OK", 200

# ============================================
# Error Handlers
# ============================================

@app.errorhandler(404)
def not_found(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    return render_template('500.html'), 500

# ============================================
# Main Entry Point
# ============================================

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)