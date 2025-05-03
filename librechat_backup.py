import os
import subprocess
import yaml
from datetime import datetime

# Configuration
BASE_DIR = "/volume1/docker/LibreChat"
BACKUP_ROOT = os.path.join(BASE_DIR, "backups")
#TIMESTAMP = datetime.now().strftime("%Y%m%d_%H%M%S")
#BACKUP_DIR = os.path.join(BACKUP_ROOT, TIMESTAMP)
BACKUP_DIR = BACKUP_ROOT

# Create backup directory structure
os.makedirs(os.path.join(BACKUP_DIR, "mongo_dump"), exist_ok=True)
os.makedirs(os.path.join(BACKUP_DIR, "pgvector_dump"), exist_ok=True)
os.makedirs(os.path.join(BACKUP_DIR, "configs"), exist_ok=True)
os.makedirs(os.path.join(BACKUP_DIR, "logs"), exist_ok=True)

def run_command(command):
    """Run a shell command with sudo"""
    try:
        result = subprocess.run(
            ["sudo"] + command,
            check=True,
            text=True,
            capture_output=True
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"Error running command: {e}")
        exit(1)

def get_container_id(service_name):
    """Get container ID for a service"""
    return run_command([
        "docker", "ps", 
        "--filter", f"name={service_name}",
        "--format", "{{.ID}}"
    ])

def sanitize_env_file(src, dst):
    """Sanitize .env file by removing sensitive keys"""
    sensitive_keys = [
        'OPENAI_API_KEY', 'MEILI_MASTER_KEY', 
        'JWT_SECRET', 'SECRET', 'PASSWORD'
    ]
    
    with open(src, 'r') as f:
        lines = f.readlines()
    
    sanitized = []
    for line in lines:
        if any(line.startswith(f"{key}=") for key in sensitive_keys):
            continue
        sanitized.append(line)
    
    with open(dst, 'w') as f:
        f.writelines(sanitized)

def backup_mongodb():
    """Backup MongoDB data"""
    print("Backing up MongoDB...")
    
    # Get MongoDB container ID
    container_id = get_container_id("mongo")
    if not container_id:
        print("MongoDB container not found")
        return

    # Create dump inside container
    run_command([
        "docker", "exec", container_id,
        "mongodump", "--db", "LibreChat", "--out", "/tmp/mongo_dump"
    ])
    
    # Copy dump to host
    run_command([
        "docker", "cp", 
        f"{container_id}:/tmp/mongo_dump", 
        os.path.join(BACKUP_DIR, "mongo_dump")
    ])

def backup_postgres():
    """Backup PostgreSQL (pgvector) data"""
    print("Backing up PostgreSQL...")
    
    # Parse docker-compose.override.yml
    compose_path = os.path.join(BASE_DIR, "docker-compose.override.yml")
    with open(compose_path, 'r') as f:
        compose = yaml.safe_load(f)
    
    # Get PostgreSQL credentials
    env_vars = compose['services']['vectordb']['environment']
    
    # Handle both list (VAR=VAL) and dictionary formats
    if isinstance(env_vars, list):
        pg_config = {k: v for item in env_vars for k, v in [item.split('=', 1)]}
    elif isinstance(env_vars, dict):
        pg_config = env_vars
    else:
        raise ValueError("Unexpected environment variables format")
    
    # Get container ID
    container_id = get_container_id("vectordb")
    if not container_id:
        print("PostgreSQL container not found")
        return

    # Create dump inside container
    run_command([
        "docker", "exec", "-e", f"PGPASSWORD={pg_config['POSTGRES_PASSWORD']}",
        container_id, "pg_dump", "-U", pg_config['POSTGRES_USER'],
        "-d", pg_config['POSTGRES_DB'], "-f", "/tmp/pgvector_dump.sql"
    ])
    
    # Copy dump to host
    run_command([
        "docker", "cp",
        f"{container_id}:/tmp/pgvector_dump.sql",
        os.path.join(BACKUP_DIR, "pgvector_dump/pgvector_dump.sql")
    ])

def backup_configs():
    """Backup and sanitize configuration files"""
    print("Backing up config files...")
    
    # Sanitize and copy .env
    sanitize_env_file(
        os.path.join(BASE_DIR, ".env"),
        os.path.join(BACKUP_DIR, "configs/.env")
    )
    
    # Copy docker-compose.override.yml
    run_command([
        "cp", 
        os.path.join(BASE_DIR, "docker-compose.override.yml"),
        os.path.join(BACKUP_DIR, "configs/")
    ])
    
    # Sanitize librechat.yaml
    librechat_path = os.path.join(BASE_DIR, "librechat.yaml")
    with open(librechat_path, 'r') as f:
        config = yaml.safe_load(f)
    
    # Remove sensitive keys (modify as needed)
    sensitive_keys = ['supportedIds', 'jwtSecret']
    for key in sensitive_keys:
        if key in config:
            del config[key]
    
    with open(os.path.join(BACKUP_DIR, "configs/librechat.yaml"), 'w') as f:
        yaml.dump(config, f)

def backup_logs():
    """Backup log files"""
    print("Backing up logs...")
    run_command([
        "cp", "-r",
        os.path.join(BASE_DIR, "logs"),
        os.path.join(BACKUP_DIR, "logs")
    ])

if __name__ == "__main__":
    # Validate sudo permissions
    run_command(["echo", "Testing sudo access..."])
    
    # Perform backups
    backup_mongodb()
    backup_postgres()
    backup_configs()
    backup_logs()
    
    print(f"Backup completed successfully in: {BACKUP_DIR}")

