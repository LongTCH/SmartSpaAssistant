import os

from dotenv import load_dotenv

# Tải biến môi trường từ .env
DOTENV_FILE = os.getenv("DOTENV_FILE", ".env")
load_dotenv(dotenv_path=DOTENV_FILE)

# Facebook Messenger config
SERVER_PORT = int(os.getenv("SERVER_PORT", 8080))
CLIENT_URLS = os.getenv("CLIENT_URLS", "*")
API_VERSION = os.getenv("API_VERSION", "v2")
PAGE_ACCESS_TOKEN = os.getenv("PAGE_ACCESS_TOKEN", "test")
VERIFY_TOKEN = os.getenv("VERIFY_TOKEN", "test")
PAGE_ID = os.getenv("PAGE_ID", "")
DATABASE_URL = os.getenv("DATABASE_URL", "")
QDRANT_URL = os.getenv("QDRANT_URL", "")
QDRANT_SCRIPT_COLLECTION_NAME = os.getenv("QDRANT_SCRIPT_COLLECTION_NAME", "test")
QDRANT_SHEET_COLLECTION_NAME = os.getenv("QDRANT_SHEET_COLLECTION_NAME", "test")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "test")
GEMINI_API_KEY = "AIzaSyDannSPDve7pk6nmfnn84pcq60GUkhn8os"
JINA_API_KEY = os.getenv("JINA_API_KEY", "test")
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "test")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "test")
CLOUDINARY_API_KEY = os.getenv("CLOUDINARY_API_KEY", "test")
CLOUDINARY_API_SECRET = os.getenv("CLOUDINARY_API_SECRET", "test")
CLOUDINARY_CLOUD_NAME = os.getenv("CLOUDINARY_CLOUD_NAME", "test")
