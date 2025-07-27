import sqlite3
import json
from uuid import uuid4
import pymongo

from core.mongo import get_mongo_db
from core.time_utils import convert_mongodb_time_to_epoch_seconds
import config

def migrate_conversations(log_callback=print):
    """
    Migrates conversations from LibreChat (MongoDB) to Open WebUI (SQLite).
    """
    mongo_db, mongo_client = get_mongo_db()
    if not mongo_db:
        log_callback("MongoDB connection failed. Aborting migration.")
        return

    sqlite_db_path = config.SQLITE_DB_PATH
    target_user_id = config.TARGET_USER_ID

    if not target_user_id or "your_open_webui_user_id" in target_user_id:
        log_callback("Error: TARGET_USER_ID is not set in the .env file.")
        mongo_client.close()
        return
        
    if not sqlite_db_path or "path/to/your/webui.db" in sqlite_db_path:
        log_callback("Error: SQLITE_DB_PATH is not set in the .env file.")
        mongo_client.close()
        return

    try:
        sqlite_conn = sqlite3.connect(sqlite_db_path)
        sqlite_conn.row_factory = sqlite3.Row
        sqlite_cursor = sqlite_conn.cursor()
        log_callback(f"Successfully connected to SQLite database: {sqlite_db_path}")
    except sqlite3.Error as e:
        log_callback(f"Error connecting to SQLite database: {e}")
        mongo_client.close()
        return

    librechat_conv_collection = mongo_db["conversations"]
    librechat_msg_collection = mongo_db["messages"]

    log_callback("Starting conversation migration...")
    migrated_count = 0
    skipped_count = 0

    for conv in librechat_conv_collection.find():
        try:
            librechat_conv_uuid = conv.get('conversationId')
            title = conv.get('title', 'Imported Conversation')
            created_at_epoch = convert_mongodb_time_to_epoch_seconds(conv.get('createdAt'))
            updated_at_epoch = convert_mongodb_time_to_epoch_seconds(conv.get('updatedAt'))
            model_name = conv.get('model', None)

            log_callback(f"\nProcessing LibreChat conversation: {title} (ID: {librechat_conv_uuid})")

            messages = list(librechat_msg_collection.find(
                {'conversationId': librechat_conv_uuid}
            ).sort('createdAt', pymongo.ASCENDING))

            if not messages:
                log_callback("  Conversation has no messages, skipping.")
                skipped_count += 1
                continue

            open_webui_messages = []
            models_in_chat = {model_name} if model_name else set()

            for msg in messages:
                role = "assistant" if not msg.get('isCreatedByUser', False) else "user"
                msg_content = msg.get('text', '')
                msg_timestamp_epoch = convert_mongodb_time_to_epoch_seconds(msg.get('createdAt'))
                msg_id = msg.get('messageId')
                parent_id = msg.get('parentMessageId')
                if parent_id == "00000000-0000-0000-0000-000000000000":
                    parent_id = None
                
                msg_model = msg.get('model')
                if msg_model:
                    models_in_chat.add(msg_model)

                open_webui_messages.append({
                    "id": msg_id,
                    "parentId": parent_id,
                    "role": role,
                    "content": msg_content,
                    "model": msg_model if role == 'assistant' else None,
                    "timestamp": msg_timestamp_epoch,
                })

            chat_json_data = {
                "id": "",
                "title": title,
                "models": list(models_in_chat),
                "params": {},
                "messages": open_webui_messages,
                "tags": conv.get('tags', []),
                "timestamp": created_at_epoch * 1000,
                "files": []
            }

            new_chat_id = str(uuid4())
            chat_json_string = json.dumps(chat_json_data, ensure_ascii=False)
            meta_json = json.dumps({})
            folder_id = None

            sql = """
            INSERT INTO chat (id, user_id, title, archived, created_at, updated_at, chat, pinned, meta, folder_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            params = (
                new_chat_id,
                target_user_id,
                title,
                0,
                created_at_epoch,
                updated_at_epoch,
                chat_json_string,
                0,
                meta_json,
                folder_id
            )

            sqlite_cursor.execute(sql, params)
            log_callback(f"  Successfully inserted conversation '{title}' into Open WebUI (New ID: {new_chat_id})")
            migrated_count += 1

        except Exception as e:
            log_callback(f"  Error processing conversation {conv.get('conversationId')}: {e}")
            skipped_count += 1
        
        if migrated_count > 0 and migrated_count % 50 == 0:
            log_callback("  Committing current transaction...")
            sqlite_conn.commit()

    log_callback(f"\nMigration complete. Migrated: {migrated_count}, Skipped/Failed: {skipped_count}.")
    log_callback("Committing final transaction...")
    sqlite_conn.commit()
    sqlite_cursor.close()
    sqlite_conn.close()
    mongo_client.close()
    log_callback("Database connections closed.")

if __name__ == '__main__':
    migrate_conversations()
