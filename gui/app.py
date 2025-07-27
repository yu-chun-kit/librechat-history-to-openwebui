import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog
import threading
import queue
import os

import config
from scripts.migrate_conversations import migrate_conversations
from scripts.generate_presets import generate_presets
from scripts.backup_librechat import backup_librechat

class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("LibreChat to Open WebUI Migration Tool")
        self.geometry("800x650")

        self.log_queue = queue.Queue()

        # --- Main Frame ---
        main_frame = ctk.CTkFrame(self)
        main_frame.pack(padx=20, pady=20, fill="both", expand=True)

        # --- Configuration Frame ---
        config_frame = ctk.CTkFrame(main_frame)
        config_frame.pack(padx=10, pady=10, fill="x")

        ctk.CTkLabel(config_frame, text="Configuration", font=("Arial", 16, "bold")).pack(anchor="w", pady=5)

        # LibreChat Docker Path
        ctk.CTkLabel(config_frame, text="LibreChat Docker Path:").pack(anchor="w")
        librechat_path_frame = ctk.CTkFrame(config_frame)
        librechat_path_frame.pack(fill="x", expand=True)
        self.librechat_path_entry = ctk.CTkEntry(librechat_path_frame, width=350)
        self.librechat_path_entry.pack(side="left", fill="x", expand=True)
        self.librechat_path_entry.insert(0, config.LIBRECHAT_DOCKER_PATH or "")
        ctk.CTkButton(librechat_path_frame, text="Browse...", command=self.browse_librechat_path).pack(side="left", padx=5)

        # MongoDB URI
        ctk.CTkLabel(config_frame, text="Mongo URI:").pack(anchor="w")
        self.mongo_uri_entry = ctk.CTkEntry(config_frame, width=400)
        self.mongo_uri_entry.pack(fill="x", expand=True)
        self.mongo_uri_entry.insert(0, config.MONGO_URI)

        # MongoDB Name
        ctk.CTkLabel(config_frame, text="Mongo DB Name:").pack(anchor="w")
        self.mongo_db_name_entry = ctk.CTkEntry(config_frame, width=400)
        self.mongo_db_name_entry.pack(fill="x", expand=True)
        self.mongo_db_name_entry.insert(0, config.MONGO_DB_NAME)

        # Target User ID
        ctk.CTkLabel(config_frame, text="Open WebUI Target User ID:").pack(anchor="w")
        self.target_user_id_entry = ctk.CTkEntry(config_frame, width=400)
        self.target_user_id_entry.pack(fill="x", expand=True)
        self.target_user_id_entry.insert(0, config.TARGET_USER_ID or "")
        
        # SQLite DB Path
        ctk.CTkLabel(config_frame, text="Open WebUI SQLite DB Path:").pack(anchor="w")
        sqlite_frame = ctk.CTkFrame(config_frame)
        sqlite_frame.pack(fill="x", expand=True)
        self.sqlite_db_path_entry = ctk.CTkEntry(sqlite_frame, width=350)
        self.sqlite_db_path_entry.pack(side="left", fill="x", expand=True)
        self.sqlite_db_path_entry.insert(0, config.SQLITE_DB_PATH or "")
        ctk.CTkButton(sqlite_frame, text="Browse...", command=self.browse_sqlite_db).pack(side="left", padx=5)

        # Output Dir
        ctk.CTkLabel(config_frame, text="Output Directory (for presets):").pack(anchor="w")
        output_dir_frame = ctk.CTkFrame(config_frame)
        output_dir_frame.pack(fill="x", expand=True)
        self.output_dir_entry = ctk.CTkEntry(output_dir_frame, width=350)
        self.output_dir_entry.pack(side="left", fill="x", expand=True)
        self.output_dir_entry.insert(0, config.OUTPUT_DIR)
        ctk.CTkButton(output_dir_frame, text="Browse...", command=self.browse_output_dir).pack(side="left", padx=5)

        ctk.CTkButton(config_frame, text="Save Configuration", command=self.save_config).pack(pady=10)

        # --- Actions Frame ---
        actions_frame = ctk.CTkFrame(main_frame)
        actions_frame.pack(padx=10, pady=10, fill="x")

        ctk.CTkLabel(actions_frame, text="Actions", font=("Arial", 16, "bold")).pack(anchor="w", pady=5)
        
        # Migration Action
        migrate_frame = ctk.CTkFrame(actions_frame)
        migrate_frame.pack(fill="x", pady=5)
        self.backup_before_migrate_var = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(migrate_frame, text="Backup before migrating", variable=self.backup_before_migrate_var).pack(side="left", padx=5)
        ctk.CTkButton(migrate_frame, text="Migrate Conversations", command=self.run_migration).pack(fill="x", expand=True)

        # Other Actions
        ctk.CTkButton(actions_frame, text="Generate Presets", command=lambda: self.run_task(generate_presets)).pack(fill="x", pady=5)
        ctk.CTkButton(actions_frame, text="Backup LibreChat", command=lambda: self.run_task(backup_librechat)).pack(fill="x", pady=5)


        # --- Log Frame ---
        log_frame = ctk.CTkFrame(main_frame)
        log_frame.pack(padx=10, pady=10, fill="both", expand=True)
        
        ctk.CTkLabel(log_frame, text="Logs", font=("Arial", 16, "bold")).pack(anchor="w", pady=5)
        self.log_textbox = ctk.CTkTextbox(log_frame, state="disabled", width=700, height=200)
        self.log_textbox.pack(fill="both", expand=True)

        self.after(100, self.process_log_queue)

    def browse_librechat_path(self):
        dirpath = filedialog.askdirectory(title="Select LibreChat Docker Path")
        if dirpath:
            self.librechat_path_entry.delete(0, tk.END)
            self.librechat_path_entry.insert(0, dirpath)

    def browse_sqlite_db(self):
        filepath = filedialog.askopenfilename(title="Select webui.db file", filetypes=(("Database files", "*.db"), ("All files", "*.* wurden")))
        if filepath:
            self.sqlite_db_path_entry.delete(0, tk.END)
            self.sqlite_db_path_entry.insert(0, filepath)
            
    def browse_output_dir(self):
        dirpath = filedialog.askdirectory(title="Select Output Directory")
        if dirpath:
            self.output_dir_entry.delete(0, tk.END)
            self.output_dir_entry.insert(0, dirpath)

    def save_config(self):
        new_config = {
            "LIBRECHAT_DOCKER_PATH": self.librechat_path_entry.get(),
            "MONGO_URI": self.mongo_uri_entry.get(),
            "MONGO_DB_NAME": self.mongo_db_name_entry.get(),
            "TARGET_USER_ID": self.target_user_id_entry.get(),
            "SQLITE_DB_PATH": self.sqlite_db_path_entry.get(),
            "OUTPUT_DIR": self.output_dir_entry.get()
        }
        config.update_config(new_config)
        self.log("Configuration saved to .env file.")

    def log(self, message):
        self.log_queue.put(message)

    def process_log_queue(self):
        while not self.log_queue.empty():
            message = self.log_queue.get_nowait()
            self.log_textbox.configure(state="normal")
            self.log_textbox.insert(tk.END, str(message) + "\n")
            self.log_textbox.configure(state="disabled")
            self.log_textbox.see(tk.END)
        self.after(100, self.process_log_queue)

    def run_task(self, task_function, *args):
        self.log(f"--- Starting {task_function.__name__} ---")
        thread = threading.Thread(target=task_function, args=args, kwargs={"log_callback": self.log})
        thread.daemon = True
        thread.start()

    def run_migration(self):
        def migration_flow():
            if self.backup_before_migrate_var.get():
                self.log("--- Starting Backup before Migration ---")
                backup_librechat(log_callback=self.log)
                self.log("--- Backup Finished ---")
            
            self.log("--- Starting Conversation Migration ---")
            migrate_conversations(log_callback=self.log)
            self.log("--- Migration Finished ---")

        thread = threading.Thread(target=migration_flow)
        thread.daemon = True
        thread.start()


if __name__ == "__main__":
    if not os.path.exists(".env"):
        if os.path.exists(".env.example"):
            with open(".env", "w") as f, open(".env.example", "r") as e:
                f.write(e.read())

    app = App()
    app.mainloop()

