import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    GROQ_API_KEY = os.getenv("GROQ_API_KEY")
    SUPABASE_URL = os.getenv("SUPABASE_URL")
    SUPABASE_KEY = os.getenv("SUPABASE_KEY")
    REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "default-secret-key")
    
    # LLM Settings
    LLM_MODEL = "llama-3.3-70b-versatile"
    
    # App Settings
    LOG_FILE_PATH = "app.log"
    BATCH_SIZE = 10
    WORKER_SLEEP_SECONDS = 3
    LLM_RATE_LIMIT_SECONDS = 1.5
