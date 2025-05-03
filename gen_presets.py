import pymongo
import json
import os
from uuid import uuid4
from datetime import datetime, timezone
import time # 用于处理时间戳

# --- 配置 ---
MONGO_URI = "mongodb://localhost:27017/"
MONGO_DB_NAME = "LibreChat"
TARGET_USER_ID = "2d0d3dbe-1234-abcd-9876-c23b10abce59" # <--- 务必替换!!!
OUTPUT_DIR = "open_webui_models" # 输出目录

# --- 确保输出目录存在 ---
os.makedirs(OUTPUT_DIR, exist_ok=True)

# --- 连接数据库 ---
try:
    mongo_client = pymongo.MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
    mongo_client.server_info()
    mongo_db = mongo_client[MONGO_DB_NAME]
    librechat_preset_collection = mongo_db["presets"]
    print("成功连接到 MongoDB。")
except pymongo.errors.ConnectionFailure as e:
    print(f"无法连接到 MongoDB: {e}")
    exit(1)
except pymongo.errors.ServerSelectionTimeoutError as e:
    print(f"连接 MongoDB 超时 (请检查 URI 和 PC 防火墙): {e}")
    exit(1)

# --- 辅助函数：时间戳转换 ---
def convert_mongodb_time_to_epoch_seconds(mongo_time):
    """将 MongoDB 的 ISODate 对象或字符串转换为 Unix epoch 秒 (整数)"""
    if isinstance(mongo_time, dict) and '$date' in mongo_time:
        ts_str = mongo_time['$date']
    elif isinstance(mongo_time, str):
         ts_str = mongo_time
    elif isinstance(mongo_time, datetime):
        if mongo_time.tzinfo is None:
            mongo_time = mongo_time.replace(tzinfo=timezone.utc)
        else:
            mongo_time = mongo_time.astimezone(timezone.utc)
        return int(mongo_time.timestamp())
    else:
        print(f"  警告：无法识别的时间格式: {mongo_time}, 使用当前时间。")
        return int(time.time())
    try:
        dt_object = datetime.fromisoformat(ts_str.replace('Z', '+00:00'))
        return int(dt_object.timestamp())
    except Exception as e:
        print(f"  警告：时间转换错误 for '{ts_str}': {e}, 使用当前时间。")
        return int(time.time())

# --- 转换主逻辑 ---
print(f"开始从 '{MONGO_DB_NAME}.presets' 读取并转换模型...")
count = 0
all_model = []
for preset in librechat_preset_collection.find():
    try:
        libre_title = preset.get('title', 'Untitled')
        print(f"  处理预设: {libre_title}")

        # 创建 Open WebUI 模型结构 [1]
        webui_model = {
            # "id": str(uuid4()), # 新的唯一 ID
            "id": libre_title, # 新的唯一 ID
            "user_id": TARGET_USER_ID,
            "base_model_id": preset.get('model', ''), # 或根据 model 推断，或设为 'ollama'/'openai' 等
            "name": libre_title,
            "params": {
                "temperature": preset.get('temperature', 0.8), # 使用 .get 提供默认值
                "system": preset.get('promptPrefix', ''), # 映射 promptPrefix
                # 添加其他可能存在的参数映射
                "top_p": preset.get('top_p', 1.0),
                "frequency_penalty": preset.get('frequency_penalty', 0.0),
                "presence_penalty": preset.get('presence_penalty', 0.0),
                # ... 其他 Open WebUI 支持的参数
            },
            "meta": {
                "profile_image_url": None,
                "description": f"Imported from LibreChat: {libre_title}",
                "capabilities": {
                    "vision": True,
                    "usage": False,
                    "citations": True
                },
                "suggestion_prompts": preset.get('examples', []), # 映射 examples
                "raw_modelfile_content": None,
                "tags": preset.get('tags', []),
            },
            # "model": {
            #     "id": preset.get('model', ''), # 直接映射，可能需要调整
            #     "name": libre_title,
            #      # 根据需要添加 modelfile 内容，如果 LibreChat 有类似字段
            # },
            "access_control": None,
            "is_active": True,
            "updated_at": convert_mongodb_time_to_epoch_seconds(preset.get('updatedAt')),
            "created_at": convert_mongodb_time_to_epoch_seconds(preset.get('createdAt')),
            # "public": True, # 或根据需要设置
            "user": { # 填充用户信息 [1]
                "id": TARGET_USER_ID,
                "name": "<your_name>", # replace with your name 
                "email": "<your_email>", # replace with your email
                "role": "admin",
                "profile_image_url": None # 或默认 Gravatar [1]
            }
        }

        # 清理文件名，移除不安全字符
        safe_title = "".join(c for c in libre_title if c.isalnum() or c in (' ', '_')).rstrip()
        safe_title = safe_title.replace(' ', '_')
        filename = f"Model-{safe_title}.json"
        filepath = os.path.join(OUTPUT_DIR, filename)

        # 保存为 JSON 文件
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump([webui_model], f, ensure_ascii=False, indent=2)

        print(f"    成功转换为: {filename}")
        count += 1
        all_model.append(webui_model)


    except Exception as e:
        print(f"  处理预设 '{preset.get('title', 'N/A')}' (ID: {preset.get('_id')}) 时出错: {e}")
    with open(os.path.join(OUTPUT_DIR, "all_model.json"), 'w', encoding='utf-8') as f:
        json.dump(all_model, f, ensure_ascii=False, indent=2)


print(f"\n转换完成！共转换 {count} 个模型预设，文件保存在 '{OUTPUT_DIR}' 目录中。")
mongo_client.close()
print("与 MongoDB 的连接已关闭。")
