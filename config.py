# Configuration for Instagram Downloader
import os

class Config:
    # App settings
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your-secret-key-here'
    
    # Instagram settings
    INSTAGRAM_BASE_URL = 'https://www.instagram.com'
    
    # Request settings
    REQUEST_TIMEOUT = 30
    REQUEST_HEADERS = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    # File settings
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size