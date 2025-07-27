#!/bin/bash

# Check for Python
if ! command -v python &> /dev/null
then
    echo "Python is not installed or not in PATH. Please install Python 3."
    exit 1
fi

# Install dependencies
echo "Installing dependencies from requirements.txt..."
pip install -r requirements.txt
if [ $? -ne 0 ]; then
    echo "Failed to install dependencies."
    exit 1
fi

# Check for command
if [ -z "$1" ]; then
    echo "Usage: ./run.sh [migrate|presets|gui|backup]"
    exit 1
fi

if [ "$1" == "migrate" ]; then
    echo "Running conversation migration..."
    python -m scripts.migrate_conversations
elif [ "$1" == "presets" ]; then
    echo "Running preset generation..."
    python -m scripts.generate_presets
elif [ "$1" == "gui" ]; then
    echo "Starting GUI..."
    python -m gui.app
elif [ "$1" == "backup" ]; then
    echo "Running LibreChat backup..."
    echo "NOTE: This requires sudo and Docker on a Linux/macOS system."
    python -m scripts.backup_librechat
else
    echo "Invalid command: $1"
    echo "Usage: ./run.sh [migrate|presets|gui|backup]"
    exit 1
fi

echo "Done."
