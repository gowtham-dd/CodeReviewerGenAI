import os
import shutil
import tempfile
from git import Repo
from github import Github
import requests
from pathlib import Path
import mimetypes
from typing import Dict, List, Optional
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RepoManagerAgent:
    """
    Model-Based Agent for handling GitHub repository operations
    Maintains state of cloned repos, tracks files, manages dependencies
    """
    
    def __init__(self, github_token: Optional[str] = None):
        self.github_token = github_token
        self.github_client = Github(github_token) if github_token else None
        self.temp_dir = tempfile.mkdtemp()
        self.repo_state = {}  # Track state of each repo
        
    def fetch_repo_info(self, repo_url: str) -> Dict:
        """Get repository metadata without cloning"""
        try:
            # Parse GitHub URL
            parts = repo_url.rstrip('/').split('/')
            owner, repo_name = parts[-2], parts[-1]
            
            if self.github_client:
                repo = self.github_client.get_repo(f"{owner}/{repo_name}")
                return {
                    "name": repo.name,
                    "full_name": repo.full_name,
                    "description": repo.description,
                    "language": repo.language,
                    "stars": repo.stargazers_count,
                    "forks": repo.forks_count,
                    "default_branch": repo.default_branch,
                    "size": repo.size,
                    "avatar_url": repo.owner.avatar_url
                }
            else:
                # Public API without token
                response = requests.get(f"https://api.github.com/repos/{owner}/{repo_name}")
                if response.status_code == 200:
                    data = response.json()
                    return {
                        "name": data["name"],
                        "full_name": data["full_name"],
                        "description": data["description"],
                        "language": data["language"],
                        "stars": data["stargazers_count"],
                        "forks": data["forks_count"],
                        "default_branch": data["default_branch"],
                        "size": data["size"],
                        "avatar_url": data["owner"]["avatar_url"]
                    }
        except Exception as e:
            logger.error(f"Error fetching repo info: {e}")
            return {"error": str(e)}
    
    def clone_repository(self, repo_url: str, branch: str = "main") -> str:
        """Clone repository and track state"""
        repo_id = self._generate_repo_id(repo_url)
        clone_path = os.path.join(self.temp_dir, repo_id)
        
        try:
            logger.info(f"Cloning {repo_url} to {clone_path}")
            repo = Repo.clone_from(repo_url, clone_path, branch=branch)
            
            # Track repository state
            self.repo_state[repo_id] = {
                "url": repo_url,
                "path": clone_path,
                "branch": branch,
                "files": [],
                "languages": {},
                "has_tests": False,
                "dependencies": []
            }
            
            # Analyze repository structure
            self._analyze_repo_structure(repo_id)
            
            return repo_id
            
        except Exception as e:
            logger.error(f"Error cloning repository: {e}")
            raise
    
    def _analyze_repo_structure(self, repo_id: str):
        """Analyze repository structure and update state"""
        repo_path = self.repo_state[repo_id]["path"]
        
        for root, dirs, files in os.walk(repo_path):
            for file in files:
                file_path = os.path.join(root, file)
                rel_path = os.path.relpath(file_path, repo_path)
                
                # Get file info
                file_info = {
                    "path": rel_path,
                    "extension": os.path.splitext(file)[1],
                    "size": os.path.getsize(file_path),
                    "language": self._detect_language(file)
                }
                
                self.repo_state[repo_id]["files"].append(file_info)
                
                # Track languages
                lang = file_info["language"]
                if lang:
                    self.repo_state[repo_id]["languages"][lang] = \
                        self.repo_state[repo_id]["languages"].get(lang, 0) + 1
                
                # Check for test files
                if 'test' in rel_path.lower() or 'spec' in rel_path.lower():
                    self.repo_state[repo_id]["has_tests"] = True
        
        # Detect dependencies
        self._detect_dependencies(repo_id)
    
    def _detect_dependencies(self, repo_id: str):
        """Detect project dependencies from common files"""
        repo_path = self.repo_state[repo_id]["path"]
        dependencies = []
        
        # Check for common dependency files
        dep_files = {
            'requirements.txt': 'python',
            'package.json': 'node',
            'pom.xml': 'java',
            'Cargo.toml': 'rust',
            'go.mod': 'go'
        }
        
        for filename, lang in dep_files.items():
            file_path = os.path.join(repo_path, filename)
            if os.path.exists(file_path):
                with open(file_path, 'r') as f:
                    content = f.read()
                    dependencies.append({
                        "type": lang,
                        "file": filename,
                        "content": content[:500]  # First 500 chars
                    })
        
        self.repo_state[repo_id]["dependencies"] = dependencies
    
    def _detect_language(self, filename: str) -> Optional[str]:
        """Detect programming language from file extension"""
        ext_map = {
            '.py': 'Python',
            '.js': 'JavaScript',
            '.jsx': 'JavaScript',
            '.ts': 'TypeScript',
            '.tsx': 'TypeScript',
            '.java': 'Java',
            '.cpp': 'C++',
            '.c': 'C',
            '.go': 'Go',
            '.rs': 'Rust',
            '.rb': 'Ruby',
            '.php': 'PHP',
            '.swift': 'Swift',
            '.kt': 'Kotlin'
        }
        ext = os.path.splitext(filename)[1].lower()
        return ext_map.get(ext)
    
    def get_code_files(self, repo_id: str, extensions: List[str] = None) -> List[Dict]:
        """Get all code files from repository"""
        if repo_id not in self.repo_state:
            raise ValueError(f"Repository {repo_id} not found")
        
        code_files = []
        for file_info in self.repo_state[repo_id]["files"]:
            if extensions and file_info["extension"] not in extensions:
                continue
            
            # Read file content
            file_path = os.path.join(self.repo_state[repo_id]["path"], file_info["path"])
            with open(file_path, 'r', errors='ignore') as f:
                content = f.read()
            
            code_files.append({
                **file_info,
                "content": content
            })
        
        return code_files
    
    def get_test_files(self, repo_id: str) -> List[Dict]:
        """Get test files from repository"""
        if repo_id not in self.repo_state:
            raise ValueError(f"Repository {repo_id} not found")
        
        test_files = []
        for file_info in self.repo_state[repo_id]["files"]:
            if 'test' in file_info["path"].lower() or 'spec' in file_info["path"].lower():
                file_path = os.path.join(self.repo_state[repo_id]["path"], file_info["path"])
                with open(file_path, 'r', errors='ignore') as f:
                    content = f.read()
                
                test_files.append({
                    **file_info,
                    "content": content
                })
        
        return test_files
    
    def get_repo_summary(self, repo_id: str) -> Dict:
        """Get summary of repository analysis"""
        if repo_id not in self.repo_state:
            raise ValueError(f"Repository {repo_id} not found")
        
        state = self.repo_state[repo_id]
        return {
            "url": state["url"],
            "branch": state["branch"],
            "total_files": len(state["files"]),
            "code_files": len([f for f in state["files"] if f["language"]]),
            "languages": state["languages"],
            "has_tests": state["has_tests"],
            "dependencies": state["dependencies"],
            "main_language": max(state["languages"], key=state["languages"].get) if state["languages"] else None
        }
    
    def cleanup(self, repo_id: str):
        """Remove cloned repository"""
        if repo_id in self.repo_state:
            repo_path = self.repo_state[repo_id]["path"]
            shutil.rmtree(repo_path, ignore_errors=True)
            del self.repo_state[repo_id]
    
    def _generate_repo_id(self, repo_url: str) -> str:
        """Generate unique ID for repository"""
        import hashlib
        return hashlib.md5(repo_url.encode()).hexdigest()[:10]