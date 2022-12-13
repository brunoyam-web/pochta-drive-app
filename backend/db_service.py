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


def write_creds_by_user_email(email: str, refresh_token: str) -> None:
    if not db["users"].find_one({"email": email}):
        db["users"].insert_one({"email": email, "refresh_token": refresh_token})
    else:
        db["users"].find_one_and_update(
            {"email": email}, {"$set": {"refresh_token": refresh_token}}
        )


def get_service_accounts():
    service_accounts = [
        account for account in db["service_accounts"].find({}, {"_id": False})
    ]
    return service_accounts


def get_master_emails():
    emails = [
        account["email"]
        for account in db["service_accounts"].find(
            {"type": "master"},
            {"_id": False, "refresh_token": False, "replicas.refresh_token": False},
        )
    ]
    return emails


def get_replicas(email: str):
    """Returns an array of replica service account in folowing format:

    Args:
        email (str): master drive email

    Returns:
    ```
    {
        email: str,
        refresh_token: str,
        storage_limit: int, # default value: 16106127360 (15GB)
        type: "replica",
    }[]
    ```
    """
    replicas = db["service_accounts"].find_one({"email": email})["replicas"]
    return replicas


def get_rt_by_user_email(email: str) -> str:
    return db["users"].find_one(filter={"email": email})["refresh_token"]


if __name__ == "__main__":
    pprint(get_service_accounts())

    # pprint(get_replicas("alexeykutsenko9@gmail.com"))

    # pprint(get_master_emails())
