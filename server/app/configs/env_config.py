import os

from dotenv import load_dotenv

# Tải biến môi trường từ .env
DOTENV_FILE = os.getenv("DOTENV_FILE", ".env")
load_dotenv(dotenv_path=DOTENV_FILE, override=True)

# Facebook Messenger config
SERVER_PORT = int(os.getenv("SERVER_PORT", 8080))
CLIENT_URLS = os.getenv("CLIENT_URLS")
PAGE_ACCESS_TOKEN = os.getenv("PAGE_ACCESS_TOKEN")
VERIFY_TOKEN = os.getenv("VERIFY_TOKEN")
PAGE_ID = os.getenv("PAGE_ID")
DATABASE_URL = os.getenv("DATABASE_URL")
QDRANT_URL = os.getenv("QDRANT_URL")
QDRANT_SCRIPT_COLLECTION_NAME = os.getenv("QDRANT_SCRIPT_COLLECTION_NAME")
QDRANT_SHEET_COLLECTION_NAME = os.getenv("QDRANT_SHEET_COLLECTION_NAME")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
JINA_API_KEY = os.getenv("JINA_API_KEY")
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
CLOUDINARY_API_KEY = os.getenv("CLOUDINARY_API_KEY")
CLOUDINARY_API_SECRET = os.getenv("CLOUDINARY_API_SECRET")
CLOUDINARY_CLOUD_NAME = os.getenv("CLOUDINARY_CLOUD_NAME")
