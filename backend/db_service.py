from pprint import pprint
from httplib2 import Credentials
from pymongo import MongoClient
from dotenv import load_dotenv
import os

load_dotenv(".env")

USERNAME = os.getenv("MONGO_INITDB_ROOT_USERNAME")
PASSWORD = os.getenv("MONGO_INITDB_ROOT_PASSWORD")
MONGO_PORT = os.getenv("MONGO_PORT")

client = MongoClient(f"mongodb://{USERNAME}:{PASSWORD}@localhost:{MONGO_PORT}/")
db = client.gshare


async def user_exists(email: str):
    return db["users"].find_one({"email": email})


async def write_creds_by_user_email(email: str, refresh_token: str) -> None:
    if not db["users"].find_one({"email": email}):
        db["users"].insert_one({"email": email, "refresh_token": refresh_token})
    else:
        db["users"].find_one_and_update(
            {"email": email}, {"$set": {"refresh_token": refresh_token}}
        )


async def get_service_accounts():
    service_accounts = [
        account for account in db["service_accounts"].find({}, {"_id": False})
    ]
    return service_accounts


async def get_rt_by_user_email(email: str) -> str:
    user = db["users"].find_one({"email": email}, {"_id": False})
    print(f"user {email = }")
    pprint(user)
    if "refresh_token" in user:
        return user["refresh_token"]
    return None
