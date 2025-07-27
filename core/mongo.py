import pymongo
from config import MONGO_URI, MONGO_DB_NAME

def get_mongo_db():
    """Establishes a connection to MongoDB and returns the database object."""
    try:
        mongo_client = pymongo.MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
        mongo_client.server_info()
        mongo_db = mongo_client[MONGO_DB_NAME]
        print("Successfully connected to MongoDB.")
        return mongo_db, mongo_client
    except pymongo.errors.ConnectionFailure as e:
        print(f"Could not connect to MongoDB: {e}")
        return None, None
    except pymongo.errors.ServerSelectionTimeoutError as e:
        print(f"Connection to MongoDB timed out (check URI and firewall): {e}")
        return None, None
