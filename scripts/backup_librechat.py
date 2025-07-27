import os
import subprocess
import yaml
from datetime import datetime
import config

def run_command(command, log_callback=print):
    """
    Run a shell command with sudo.
    Note: This requires sudo privileges and is designed for Linux/macOS.
    """
    try:
        log_callback(f"  Running command: {' '.join(command)}")
        result = subprocess.run(
            ["sudo"] + command,
            check=True,
            text=True,
            capture_output=True
        )
        return result.stdout.strip()
    except FileNotFoundError:
        log_callback("Error: 'sudo' command not found. This script is intended for Linux/macOS.")
        return None
    except subprocess.CalledProcessError as e:
        log_callback(f"Error running command: {e}\n  Stdout: {e.stdout}\n  Stderr: {e.stderr}")
        return None

def get_container_id(service_name, log_callback=print):
    """Get container ID for a service."""
    return run_command([
        "docker", "ps",
        "--filter", f"name={service_name}",
        "--format", "{{.ID}}"
    ], log_callback)

def backup_mongodb(base_dir, backup_dir, log_callback=print):
    """Backup MongoDB data."""
    log_callback("Backing up MongoDB...")
    container_id = get_container_id("mongo", log_callback)
    if not container_id:
        log_callback("MongoDB container not found, skipping backup.")
        return

    dump_path_host = os.path.join(backup_dir, "mongo_dump")
    os.makedirs(dump_path_host, exist_ok=True)

    # Create dump inside container
    if not run_command(["docker", "exec", container_id, "mongodump", "--db", "LibreChat", "--out", "/tmp/mongo_dump"], log_callback):
        return

    # Copy dump to host
    run_command(["docker", "cp", f"{container_id}:/tmp/mongo_dump", dump_path_host], log_callback)
    log_callback("MongoDB backup completed.")


def backup_librechat(log_callback=print):
    """
    Performs a backup of the LibreChat instance (MongoDB).
    Requires a Linux/macOS environment with sudo and Docker.
    """
    log_callback("--- Starting LibreChat Backup ---")
    log_callback("WARNING: This script requires sudo access and a Docker environment on Linux/macOS.")

    base_dir = config.LIBRECHAT_DOCKER_PATH
    if not base_dir or not os.path.isdir(base_dir):
        log_callback(f"Error: LIBRECHAT_DOCKER_PATH ('{base_dir}') is not set or not a valid directory.")
        return

    backup_root = os.path.join(base_dir, "backups")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = os.path.join(backup_root, timestamp)
    os.makedirs(backup_dir, exist_ok=True)

    log_callback(f"Backup directory: {backup_dir}")

    # Test sudo access
    if run_command(["echo", "Testing sudo access..."], log_callback) is None:
        log_callback("Sudo access test failed. Aborting backup.")
        return

    backup_mongodb(base_dir, backup_dir, log_callback)

    log_callback(f"--- Backup process finished. Files saved in: {backup_dir} ---")

if __name__ == "__main__":
    # Load config to ensure variables are available
    from dotenv import load_dotenv
    load_dotenv()
    config.LIBRECHAT_DOCKER_PATH = os.getenv("LIBRECHAT_DOCKER_PATH")
    
    backup_librechat()