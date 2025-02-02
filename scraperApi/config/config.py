from dotenv import load_dotenv
import os
load_dotenv()

OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
APP_API_KEY = os.getenv('APP_API_KEY')
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY')
PROXY_USERNAME = os.getenv('PROXY_USERNAME')
PROXY_PASSWORD = os.getenv('PROXY_PASSWORD')
OPEN_ROUTER_API = os.getenv('OPEN_ROUTER_API')
RAPID_API_HOST = os.getenv('RAPID_API_HOST')
RAPID_API_KEY = os.getenv('RAPID_API_KEY')