import json
import os
from uuid import uuid4

from core.mongo import get_mongo_db
from core.time_utils import convert_mongodb_time_to_epoch_seconds
import config

def generate_presets(log_callback=print):
    """
    Connects to a MongoDB database, reads presets from the 'presets' collection,
    and converts them into Open WebUI model format, saving each as a JSON file.
    """
    mongo_db, mongo_client = get_mongo_db()
    if not mongo_db:
        log_callback("MongoDB connection failed. Aborting preset generation.")
        return

    librechat_preset_collection = mongo_db["presets"]
    output_dir = config.OUTPUT_DIR
    target_user_id = config.TARGET_USER_ID

    if not target_user_id or "your_open_webui_user_id" in target_user_id:
        log_callback("Error: TARGET_USER_ID is not set in the .env file.")
        mongo_client.close()
        return

    os.makedirs(output_dir, exist_ok=True)
    log_callback(f"Reading presets from '{config.MONGO_DB_NAME}.presets' and converting to Open WebUI format...")

    count = 0
    all_model = []
    for preset in librechat_preset.find():
        try:
            libre_title = preset.get('title', 'Untitled')
            log_callback(f"  Processing preset: {libre_title}")

            webui_model = {
                "id": libre_title,
                "user_id": target_user_id,
                "base_model_id": preset.get('model', ''),
                "name": libre_title,
                "params": {
                    "temperature": preset.get('temperature', 0.8),
                    "system": preset.get('promptPrefix', ''),
                    "top_p": preset.get('top_p', 1.0),
                    "frequency_penalty": preset.get('frequency_penalty', 0.0),
                    "presence_penalty": preset.get('presence_penalty', 0.0),
                },
                "meta": {
                    "profile_image_url": None,
                    "description": f"Imported from LibreChat: {libre_title}",
                    "capabilities": {"vision": True, "usage": False, "citations": True},
                    "suggestion_prompts": preset.get('examples', []),
                    "raw_modelfile_content": None,
                    "tags": preset.get('tags', []),
                },
                "access_control": None,
                "is_active": True,
                "updated_at": convert_mongodb_time_to_epoch_seconds(preset.get('updatedAt')),
                "created_at": convert_mongodb_time_to_epoch_seconds(preset.get('createdAt')),
                "user": {
                    "id": target_user_id,
                    "name": "<your_name>",
                    "email": "<your_email>",
                    "role": "admin",
                    "profile_image_url": None
                }
            }

            safe_title = "".join(c for c in libre_title if c.isalnum() or c in (' ', '_')).rstrip().replace(' ', '_')
            filename = f"Model-{safe_title}.json"
            filepath = os.path.join(output_dir, filename)

            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump([webui_model], f, ensure_ascii=False, indent=2)

            log_callback(f"    Successfully converted to: {filename}")
            count += 1
            all_model.append(webui_model)

        except Exception as e:
            log_callback(f"  Error processing preset '{preset.get('title', 'N/A')}' (ID: {preset.get('_id')}): {e}")

    if all_model:
        with open(os.path.join(output_dir, "all_models.json"), 'w', encoding='utf-8') as f:
            json.dump(all_model, f, ensure_ascii=False, indent=2)

    log_callback(f"\nConversion complete! {count} presets converted and saved in '{output_dir}'.")
    mongo_client.close()
    log_callback("MongoDB connection closed.")

if __name__ == '__main__':
    generate_presets()
