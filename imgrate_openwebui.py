import pymongo
import sqlite3
import json
from uuid import uuid4
from datetime import datetime, timezone
import time # 用于处理时间戳

# --- 配置 ---
# 确保 PC 防火墙允许 NAS (192.168.128.1) 访问 27017 端口
MONGO_URI = "mongodb://localhost:27017/"
MONGO_DB_NAME = "LibreChat"
# NAS 上的路径，需要先 docker cp open-webui:/app/backend/data/webui.db . 来获取
SQLITE_DB_PATH = "/volume1/docker/open-webui/data/webui.db"
# !!! 必须在 Open WebUI 中找到你的用户 ID (通常是 UUID 字符串) !!!
# 登录 Open WebUI，检查 profile URL 或数据库 user 表
TARGET_USER_ID = "2d0d3dbe-1234-abcd-9876-c23b10abce59" # <--- 务必替换!!!

# --- 连接数据库 ---
try:
    mongo_client = pymongo.MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000) # 增加超时
    mongo_client.server_info() # 测试连接
    mongo_db = mongo_client[MONGO_DB_NAME]
    librechat_conv_collection = mongo_db["conversations"]
    librechat_msg_collection = mongo_db["messages"]
    print("成功连接到 MongoDB。")
except pymongo.errors.ConnectionFailure as e:
    print(f"无法连接到 MongoDB: {e}")
    exit(1)
except pymongo.errors.ServerSelectionTimeoutError as e:
    print(f"连接 MongoDB 超时 (请检查 URI 和 PC 防火墙): {e}")
    exit(1)


sqlite_conn = sqlite3.connect(SQLITE_DB_PATH)
sqlite_conn.row_factory = sqlite3.Row # 让结果可以按列名访问
sqlite_cursor = sqlite_conn.cursor()
print(f"成功连接到 SQLite 数据库: {SQLITE_DB_PATH}")


# --- 辅助函数：时间戳转换 ---
def convert_mongodb_time_to_epoch_seconds(mongo_time):
    """将 MongoDB 的 ISODate 对象或字符串转换为 Unix epoch 秒 (整数)"""
    if isinstance(mongo_time, dict) and '$date' in mongo_time:
        ts_str = mongo_time['$date']
    elif isinstance(mongo_time, str):
         ts_str = mongo_time
    elif isinstance(mongo_time, datetime): # pymongo 可能直接转为 datetime 对象
        # 确保是 aware datetime in UTC
        if mongo_time.tzinfo is None:
            mongo_time = mongo_time.replace(tzinfo=timezone.utc)
        else:
            mongo_time = mongo_time.astimezone(timezone.utc)
        return int(mongo_time.timestamp())
    else:
        # 提供一个默认值或记录错误
        print(f"  警告：无法识别的时间格式: {mongo_time}, 使用当前时间。")
        return int(time.time())

    try:
        # 处理 ISO 8601 格式，包括 'Z' for UTC
        dt_object = datetime.fromisoformat(ts_str.replace('Z', '+00:00'))
        return int(dt_object.timestamp())
    except Exception as e:
        print(f"  警告：时间转换错误 for '{ts_str}': {e}, 使用当前时间。")
        return int(time.time())

# --- 核心迁移逻辑 ---
print("开始迁移对话...")
migrated_count = 0
skipped_count = 0

for conv in librechat_conv_collection.find():
    try:
        librechat_conv_uuid = conv.get('conversationId') # 使用 LibreChat 的 UUID
        librechat_user_id_bson = conv.get('user') # LibreChat 的用户 BSON ID (可能不需要)
        title = conv.get('title', 'Imported Conversation')
        created_at_epoch = convert_mongodb_time_to_epoch_seconds(conv.get('createdAt'))
        updated_at_epoch = convert_mongodb_time_to_epoch_seconds(conv.get('updatedAt'))
        model_name = conv.get('model', None) # 主要模型

        print(f"\n处理 LibreChat 对话: {title} (ID: {librechat_conv_uuid})")

        # 1. 获取此对话的所有消息 (按创建时间排序)
        messages = list(librechat_msg_collection.find(
            {'conversationId': librechat_conv_uuid}
        ).sort('createdAt', pymongo.ASCENDING))

        if not messages:
            print(f"  对话没有消息，跳过。")
            skipped_count += 1
            continue

        # 2. 构建 Open WebUI 的 chat JSON 结构 (主要关注 messages 数组)
        open_webui_messages = []
        models_in_chat = set() # 收集对话中用到的所有模型
        if model_name:
              models_in_chat.add(model_name)

        for msg in messages:
            role = "assistant"
            if msg.get('isCreatedByUser', False):
                role = "user"

            msg_content = msg.get('text', '')
            msg_timestamp_epoch = convert_mongodb_time_to_epoch_seconds(msg.get('createdAt'))
            msg_id = msg.get('messageId')  # 使用 LibreChat 的 message UUID
            parent_id = msg.get('parentMessageId')
            # 对于第一条消息，LibreChat 的 parentId 可能是 '000...' 或 null
            if parent_id == "00000000-0000-0000-0000-000000000000":
                parent_id = None

            msg_model = msg.get('model') # 消息级别的模型（通常是助手消息才有）
            if msg_model:
                 models_in_chat.add(msg_model)

            # 构建 Open WebUI message 字典
            # 注意：我们简化结构，只包含 messages 数组需要的核心字段
            # 你可能需要根据 Open WebUI 的具体期望调整（比如添加 usage 等）
            open_webui_msg = {
                "id": msg_id,
                "parentId": parent_id,
                "role": role,
                "content": msg_content,
                "model": msg_model if role == 'assistant' else None, # 只有助手消息有模型
                "timestamp": msg_timestamp_epoch,
                 # 可以考虑添加 usage, finish_reason 等，如果需要的话
                # "usage": { ... }
            }
            open_webui_messages.append(open_webui_msg)

        # 构建完整的 chat JSON 对象
        chat_json_data = {
            "id": "", # 似乎不需要填？
            "title": title,
            "models": list(models_in_chat), # 对话中使用的所有模型列表
            "params": {}, # 假设没有特殊参数需要迁移
            "messages": open_webui_messages,
            # history 对象比较复杂，我们先省略，依赖 messages 数组
            # "history": { ... },
            "tags": conv.get('tags', []), # 迁移标签
            "timestamp": created_at_epoch * 1000, # OpenWebUI 内部时间戳似乎是毫秒? 验证一下
            "files": [] # 假设不迁移文件
        }

        # 3. 准备插入 Open WebUI chat 表的数据
        new_chat_id = str(uuid4()) # 为 Open WebUI 生成新的 UUID
        # Open WebUI 的 created_at/updated_at 是 DATETIME 列
        # SQLite 通常接受 ISO 8601 字符串或 epoch 秒
        # created_at_iso = datetime.fromtimestamp(created_at_epoch, timezone.utc).isoformat(timespec='milliseconds').replace('+00:00', 'Z')
        # updated_at_iso = datetime.fromtimestamp(updated_at_epoch, timezone.utc).isoformat(timespec='milliseconds').replace('+00:00', 'Z')
        chat_json_string = json.dumps(chat_json_data, ensure_ascii=False) # ensure_ascii=False 保留中文等字符

        # 4. 执行插入
        # !!! 确认 chat 表的列名和数据类型 !!!
        sql = """
        INSERT INTO chat (id, user_id, title, archived, created_at, updated_at, chat, pinned, meta, folder_id)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        # meta 和 folder_id 可能需要默认值或从 LibreChat 映射（如果存在对应字段）
        meta_json = json.dumps({}) # 默认空的 meta
        folder_id = None # 默认没有文件夹

        # 假设 archived 和 pinned 默认为 False (0)
        params = (
            new_chat_id,
            # TARGET_USER_ID,
            "2d0d3dbe-6c7c-4f16-aedc-c23b10cade59",
            title,
            0, # archived (False)
            # created_at_iso, # 使用 ISO 格式字符串
            # updated_at_iso, # 使用 ISO 格式字符串
            created_at_epoch,
            updated_at_epoch,
            chat_json_string, # 核心的 JSON 数据
            0, # pinned (False)
            meta_json, # 默认空 meta
            folder_id # 默认 null folder
        )

        sqlite_cursor.execute(sql, params)
        print(f"  成功将对话 '{title}' 插入 Open WebUI (New ID: {new_chat_id})")
        migrated_count += 1

    except Exception as e:
        print(f"  处理 LibreChat 对话 {conv.get('conversationId')} 时出错: {e}")
        print(f"  Conversation Data: {conv}") # 打印出问题的数据帮助调试
        skipped_count += 1
    finally:
        # 定期提交，避免事务过大（可选）
        if migrated_count > 0 and migrated_count % 50 == 0:
             print("  提交当前事务...")
             sqlite_conn.commit()


# --- 清理与收尾 ---
print(f"\n迁移完成。成功迁移 {migrated_count} 个对话，跳过/失败 {skipped_count} 个。")
print("最后提交事务...")
sqlite_conn.commit() # 确保所有更改都已提交
sqlite_cursor.close()
sqlite_conn.close()
mongo_client.close()
print("数据库连接已关闭。")

