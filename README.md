
# 🚀 AI Code Reviewer - Multi-Agent System

![AI Code Reviewer](https://img.shields.io/badge/AI-Code%20Reviewer-indigo)
![Flask](https://img.shields.io/badge/Flask-2.3.3-green)
![LangChain](https://img.shields.io/badge/LangChain-0.1.0-blue)
![Groq](https://img.shields.io/badge/Groq-LLM-orange)

## 📺 Watch the Demo

[![AI Code Reviewer Demo](https://img.shields.io/badge/YouTube-Watch%20Demo-red)](https://youtu.be/YOUR_VIDEO_ID_HERE)

Click the badge above or [watch this video](https://www.youtube.com/watch?v=bqSY-kNAABQ) to see the AI Code Reviewer in action!

## 📋 Table of Contents
- [Overview](#-overview)
- [System Architecture](#-system-architecture)
- [Features](#-features)
- [Tech Stack](#-tech-stack)
- [Installation](#-installation)
- [Configuration](#-configuration)
- [Usage Guide](#-usage-guide)
- [Agent Workflows](#-agent-workflows)
- [API Reference](#-api-reference)
- [Project Structure](#-project-structure)
- [Impact & Use Cases](#-impact--use-cases)
- [Future Enhancements](#-future-enhancements)
- [Contributing](#-contributing)
- [License](#-license)

## 🎯 Overview

**AI Code Reviewer** is a cutting-edge multi-agent system that leverages the power of Large Language Models (LLMs) and static code analysis to provide comprehensive code reviews. Unlike traditional code review tools, this system employs **5 specialized AI agents** working in concert to evaluate code from multiple dimensions:

- **Correctness** - Test execution and validation
- **Complexity** - Time & space complexity analysis
- **Readability** - Code style and best practices
- **Edge Cases** - Comprehensive test scenario generation
- **Summarization** - Human-like feedback synthesis

The system can analyze both **pasted code snippets** and **entire GitHub repositories**, making it versatile for individual developers, teams, and educational institutions.

## 🏗 System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      USER INTERFACE                           │
│            (Web Dashboard - Flask + Tailwind)                 │
└─────────────────────────┬───────────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────────┐
│                    ORCHESTRATOR (LangGraph)                   │
│              Manages agent communication & workflow           │
└─────────┬──────────┬──────────┬──────────┬──────────┬───────┘
          │          │          │          │          │
┌─────────▼──┐ ┌─────▼─────┐ ┌─▼────────┐ ┌▼─────────┐ ┌▼────────┐
│ Agent 1    │ │ Agent 2   │ │ Agent 3  │ │ Agent 4  │ │ Agent 5 │
│Correctness │ │Complexity │ │Readability││Edge Cases││Summarizer│
└─────────┬──┘ └─────┬─────┘ └─┬────────┘ └▼─────────┘ └──┬─────┘
          │          │          │          │               │
          └──────────┴──────────┴──────────┴───────────────┘
                          │
┌─────────────────────────▼───────────────────────────────────┐
│                      Groq LLM LLAMA3                 │
│                 Powers all agent intelligence                 │
└─────────────────────────────────────────────────────────────┘
```

## ✨ Features

### 🤖 **5 Specialized AI Agents**

| Agent | Function | Real/Simulated |
|-------|----------|----------------|
| **Agent 1: Correctness** | Runs test cases, validates outputs | ✅ **Real** |
| **Agent 2: Complexity** | Analyzes time & space complexity | ✅ **Real** |
| **Agent 3: Readability** | Reviews code style & best practices | ⭐ **Premium** |
| **Agent 4: Edge Cases** | Generates comprehensive test scenarios | ⭐ **Premium** |
| **Agent 5: Summarizer** | Provides human-like feedback | ⭐ **Premium** |

### 📊 **Dashboard & Analytics**
- **Overall Score** - Percentage-based code quality metric
- **Radar Chart** - Visual representation of 6 quality dimensions
- **Industry Benchmark** - Compare against Junior/Mid/Senior levels
- **Recent Reviews** - Track your improvement over time

### 🔗 **GitHub Integration**
- Paste any public repository URL
- Automatic language detection
- Preview repo stats (stars, forks, language)
- Simulation data for quick demonstration

### 🎨 **Professional UI**
- Glass-morphism design
- Responsive layout (mobile & desktop)
- CodeMirror editor with syntax highlighting
- Real-time loading indicators
- Tabbed results interface

## 🛠 Tech Stack

### **Backend**
- **Flask 2.3.3** - Web framework
- **LangChain 0.1.0** - LLM orchestration
- **LangGraph 0.0.20** - Agent workflow management
- **Groq API** - LLM provider (Mixtral-8x7B)
- **Celery** - Async task queue
- **Redis** - Caching & message broker

### **Frontend**
- **TailwindCSS** - Styling
- **CodeMirror** - Code editor
- **Chart.js** - Data visualization
- **Font Awesome** - Icons

### **Code Analysis**
- **Radon** - Cyclomatic complexity
- **Pylint** - Python style guide
- **Black** - Code formatting
- **AST** - Abstract Syntax Tree parsing

## 📦 Installation

### Prerequisites
- Python 3.9+
- Git
- Groq API Key (free)

### Step-by-Step Setup

1. **Clone the repository**
```bash
git clone https://github.com/gowtham-dd/CodeReviewerGenAI
cd ai-code-reviewer
```

2. **Create virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Set up environment variables**
```bash
cp .env.example .env
# Edit .env with your Groq API key
```

5. **Run the application**
```bash
python app.py
```

6. **Access the application**
```
http://localhost:5000
```

## 🔑 Configuration

### Environment Variables (.env)

```env
# Groq API Configuration (REQUIRED)
GROQ_API_KEY=your-groq-api-key-here
GROQ_MODEL=llama-3.1-8b-instant

# GitHub Token (Optional - for higher API limits)
GITHUB_TOKEN=your-github-token-here

# Flask Configuration
SECRET_KEY=your-secret-key-here
FLASK_ENV=development
FLASK_APP=app.py
```

### Getting a Groq API Key

1. Visit [Groq Console](https://console.groq.com)
2. Sign up for a free account
3. Navigate to API Keys section
4. Create a new API key
5. Copy and paste into your `.env` file

**Free Tier Limits:**
- 3-5 requests per minute
- 50-100 requests per day
- Perfect for development and testing!

## 🚀 Usage Guide

### **Reviewing Code**
1. Navigate to **Review Code** page
2. Select programming language
3. Paste your code in the editor
4. Click **Start Review**
5. View comprehensive results across 5 tabs

### **Analyzing GitHub Repositories**
1. Navigate to **GitHub Repo** page
2. Paste repository URL (e.g., `https://github.com/gowtham-dd/CodeReviewerGenAI`)
3. Wait for preview to load
4. Click **Analyze Repository**
5. View simulation results

### **Understanding Results**

#### **Correctness Tab**
- Test cases run against your code
- Pass/fail indicators
- Error messages for failed tests

#### **Complexity Tab**
- Time complexity (Big O notation)
- Space complexity analysis
- Hotspot identification
- Optimization suggestions

#### **Readability Tab (Premium)**
- Style score (0-10)
- Documentation score
- Naming convention analysis
- Improvement suggestions

#### **Edge Cases Tab (Premium)**
- Boundary value tests
- Invalid input scenarios
- Stress test recommendations
- Severity ratings

#### **Summary Tab (Premium)**
- Executive summary
- Key findings
- Improvement roadmap
- Optimized code suggestions

## 🤖 Agent Workflows

### **Agent 1: Correctness** (Simple Reflex + Goal-Based)
```python
Input: Code + Test Cases
Process: 
  - Execute code against test cases
  - Validate outputs
  - Catch exceptions
Output: Test results with pass/fail metrics
```

### **Agent 2: Complexity** (Model-Based + Utility)
```python
Input: Code
Process:
  - Parse AST
  - Detect nested loops
  - Analyze recursion
  - Calculate cyclomatic complexity
Output: Time & space complexity with explanations
```

### **Agent 3: Readability** (Goal-Based + Learning) - *Premium*
```python
Input: Code
Process:
  - Check naming conventions
  - Analyze documentation
  - Evaluate code structure
  - Compare against best practices
Output: Readability scores and suggestions
```

### **Agent 4: Edge Cases** (Utility-Based) - *Premium*
```python
Input: Code + Function Signature
Process:
  - Generate boundary values
  - Create invalid inputs
  - Design stress tests
  - Prioritize by severity
Output: Comprehensive test scenarios
```

### **Agent 5: Summarizer** (Learning + Utility) - *Premium*
```python
Input: All agent reports
Process:
  - Synthesize findings
  - Prioritize issues
  - Generate recommendations
  - Create optimized code
Output: Human-readable summary
```

## 📡 API Reference

### **Code Review Endpoints**

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/review` | POST | Submit code for review |
| `/api/review/<review_id>` | GET | Get review results |
| `/api/user/history` | GET | Get user review history |

### **GitHub Endpoints**

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/repo-info` | GET | Get repository metadata |
| `/api/analyze-repo` | POST | Analyze GitHub repository |

### **Premium Endpoints**

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/premium-review` | POST | Premium 5-agent review |
| `/api/upgrade-prompt` | GET | Get premium features info |

## 📁 Project Structure

```
ai-code-reviewer/
├── app.py                 # Main Flask application
├── config.py              # Configuration
├── requirements.txt       # Dependencies
├── .env                   # Environment variables
├── .gitignore            # Git ignore file
├── agents/                # AI Agents
│   ├── __init__.py
│   ├── correctness.py    # Agent 1
│   ├── complexity.py     # Agent 2
│   ├── readability.py    # Agent 3 (Premium)
│   ├── edge_cases.py     # Agent 4 (Premium)
│   ├── summarizer.py     # Agent 5 (Premium)
│   ├── repo_manager.py   # GitHub handler
│   └── graph.py          # LangGraph workflow
├── templates/            # HTML templates
│   ├── base.html
│   ├── index.html
│   ├── dashboard.html
│   ├── review.html
│   ├── github.html
│   ├── premium.html
│   ├── review_result.html
│   ├── 404.html
│   └── 500.html
├── static/               # Static assets
│   ├── css/
│   │   └── style.css
│   └── js/
│       └── main.js
└── temp_repos/          # Temporary repo storage
```

## 💡 Impact & Use Cases

### **For Individual Developers**
- **Skill Development**: Understand your code quality
- **Interview Prep**: Practice with professional feedback
- **Learning**: See optimized versions of your code

### **For Educational Institutions**
- **Bootcamps**: Automate student code reviews
- **Universities**: Scale CS education
- **Coding Schools**: Provide consistent feedback

### **For Teams**
- **Code Quality**: Maintain standards across projects
- **Onboarding**: Help new team members learn patterns
- **Code Reviews**: Augment human reviewers

### **Business Impact**
- **Time Savings**: 80% faster than manual reviews
- **Consistency**: Standardized feedback
- **Scalability**: Review 100x more code
- **Learning**: Continuous improvement

## 🚀 Future Enhancements

### **Short Term**
- [ ] Add support for more languages (Java, Go, Rust)
- [ ] Implement real GitHub file fetching
- [ ] Add user authentication
- [ ] Create team dashboards

### **Medium Term**
- [ ] Premium subscription model
- [ ] CI/CD integration (GitHub Actions)
- [ ] VS Code extension
- [ ] Historical trend analysis

### **Long Term**
- [ ] Custom rule creation
- [ ] Team collaboration features
- [ ] Enterprise SSO
- [ ] AI-powered code generation

## 🤝 Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

### **Development Guidelines**
- Follow PEP 8 style guide
- Add tests for new features
- Update documentation
- Use conventional commits
