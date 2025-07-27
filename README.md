# LibreChat to Open WebUI Migration Tool

This tool helps you migrate your conversation history and presets from LibreChat to Open WebUI. It provides a graphical user interface (GUI) for ease of use, as well as command-line scripts for automation.

## Features

-   Migrate conversation history from a MongoDB backup of LibreChat to an Open WebUI SQLite database.
-   Generate Open WebUI compatible preset files from your LibreChat presets.
-   **Backup your LibreChat MongoDB database** using Docker (requires Linux/macOS and sudo).
-   Easy configuration using a `.env` file.
-   User-friendly GUI for configuration and execution.
-   CLI scripts for power users and automation.

## Prerequisites

-   Python 3.6+
-   A running LibreChat instance in Docker (for the backup feature).
-   A MongoDB backup of your LibreChat database.
-   Access to your Open WebUI `webui.db` SQLite file.
-   For the backup feature: A Linux or macOS environment with `sudo` and `docker` installed.

## Installation

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/your-username/librechat-history-to-openwebui.git
    cd librechat-history-to-openwebui
    ```

2.  **Create a `.env` file:**
    Copy the `.env.example` file to a new file named `.env`.
    ```bash
    # On Windows
    copy .env.example .env

    # On Linux/macOS
    cp .env.example .env
    ```

3.  **Edit the `.env` file:**
    Open the `.env` file in a text editor and fill in your specific details:
    -   `MONGO_URI`: The connection string for your MongoDB database.
    -   `MONGO_DB_NAME`: The name of your LibreChat database.
    -   `TARGET_USER_ID`: Your user ID in Open WebUI. You can find this in your profile URL or by inspecting the `user` table in the `webui.db` file.
    -   `SQLITE_DB_PATH`: The absolute path to your Open WebUI `webui.db` file.
    -   `OUTPUT_DIR`: The directory where the generated preset files will be saved.

4.  **Install dependencies:**
    The provided scripts will attempt to install the required Python packages automatically. You can also install them manually:
    ```bash
    pip install -r requirements.txt
    ```

## Usage

You can use this tool via the GUI or the command line.

### GUI Mode

To run the application in GUI mode, use the following command:

```bash
# On Windows
run.bat gui

# On Linux/macOS
./run.sh gui
```

The GUI allows you to:
-   View and update your configuration.
-   Save your settings to the `.env` file.
-   Browse for your `webui.db` file and output directory.
-   Run the "Migrate Conversations" and "Generate Presets" tasks with the click of a button.
-   Run a backup of your LibreChat Docker instance.
-   View logs of the operations in real-time.

### Command-Line (CLI) Mode

The CLI is ideal for automation or for users who prefer the command line.

**Migrate Conversations:**
```bash
# On Windows
run.bat migrate

# On Linux/macOS
./run.sh migrate
```

**Generate Presets:**
```bash
# On Windows
run.bat presets

# On Linux/macOS
./run.sh presets
```

**Backup LibreChat:**
> **Note:** This command requires a Linux/macOS environment with `sudo` and `docker`.
```bash
# On Linux/macOS
./run.sh backup
```

## How it Works

### Backup
The backup script (`scripts/backup_librechat.py`) connects to your Docker instance to create a `mongodump` of the LibreChat database. It saves the backup to a `backups` folder inside your main LibreChat directory.

### Conversation Migration

The migration script (`scripts/migrate_conversations.py`) performs the following steps:
1.  Connects to your LibreChat MongoDB database.
2.  Reads conversations and their corresponding messages.
3.  Connects to your Open WebUI SQLite database.
4.  Formats the conversation data into the structure required by Open WebUI.
5.  Inserts the formatted data into the `chat` table in the `webui.db` file.

### Preset Generation

The preset generation script (`scripts/generate_presets.py`) performs the following steps:
1.  Connects to your LibreChat MongoDB database.
2.  Reads your saved presets from the `presets` collection.
3.  Converts each preset into an Open WebUI compatible JSON model file.
4.  Saves the generated files to the specified output directory.

## Contributing

Contributions are welcome! Please feel free to submit a pull request or open an issue if you find a bug or have a feature request.
