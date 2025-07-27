import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# --- LibreChat Docker Path ---
LIBRECHAT_DOCKER_PATH = os.getenv("LIBRECHAT_DOCKER_PATH")

# --- MongoDB Configuration ---
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
MONGO_DB_NAME = os.getenv("MONGO_DB_NAME", "LibreChat")

# --- Open WebUI Configuration ---
TARGET_USER_ID = os.getenv("TARGET_USER_ID")
SQLITE_DB_PATH = os.getenv("SQLITE_DB_PATH")

# --- Output Configuration ---
OUTPUT_DIR = os.getenv("OUTPUT_DIR", "open_webui_presets")

def get_config():
    """Returns a dictionary of the current configuration."""
    return {
        "MONGO_URI": MONGO_URI,
        "MONGO_DB_NAME": MONGO_DB_NAME,
        "TARGET_USER_ID": TARGET_USER_ID,
        "SQLITE_DB_PATH": SQLITE_DB_PATH,
        "OUTPUT_DIR": OUTPUT_DIR,
    }

def update_config(new_config):
    """Updates the configuration variables."""
    global MONGO_URI, MONGO_DB_NAME, TARGET_USER_ID, SQLITE_DB_PATH, OUTPUT_DIR
    MONGO_URI = new_config.get("MONGO_URI", MONGO_URI)
    MONGO_DB_NAME = new_config.get("MONGO_DB_NAME", MONGO_DB_NAME)
    TARGET_USER_ID = new_config.get("TARGET_USER_ID", TARGET_USER_ID)
    SQLITE_DB_PATH = new_config.get("SQLITE_DB_PATH", SQLITE_DB_PATH)
    OUTPUT_DIR = new_config.get("OUTPUT_DIR", OUTPUT_DIR)

    # Update .env file
    with open(".env", "w") as f:
        f.write(f"MONGO_URI={MONGO_URI}\n")
        f.write(f"MONGO_DB_NAME={MONGO_DB_NAME}\n")
        f.write(f"TARGET_USER_ID={TARGET_USER_ID}\n")
        f.write(f"SQLITE_DB_PATH={SQLITE_DB_PATH}\n")
        f.write(f"OUTPUT_DIR={OUTPUT_DIR}\n")
