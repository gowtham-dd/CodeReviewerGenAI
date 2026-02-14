import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key')
    
    # Groq Configuration
    GROQ_API_KEY = os.getenv('GROQ_API_KEY', 'your-groq-api-key')
    GROQ_MODEL = "llama-3.1-8b-instant"  # or "llama2-70b-4096"
    
    # GitHub Configuration
    GITHUB_TOKEN = os.getenv('GITHUB_TOKEN', '')
    
    # Redis Configuration (for caching)
    REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
    
    # Upload folder for cloned repos
    UPLOAD_FOLDER = 'temp_repos'
    ALLOWED_EXTENSIONS = {'py', 'js', 'java', 'cpp', 'go', 'rs', 'rb'}
    
    # Agent Configuration
    MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB
    TIMEOUT_SECONDS = 300