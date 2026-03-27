import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
VECTOR_STORE_ID = os.getenv("VECTOR_STORE_ID", "")

PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT.parent / "data"
OUTPUT_DIR = PROJECT_ROOT / "output"
OUTPUT_DIR.mkdir(exist_ok=True)

PRODUCTS_CSV = DATA_DIR / "midnight_products.csv"
ORDERS_CSV = DATA_DIR / "midnight_orders.csv"
RETURN_POLICY = DATA_DIR / "midnight_return_policy.md"
