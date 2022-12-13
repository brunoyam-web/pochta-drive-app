import logging
import os
from flask import Flask, request
import db_service
from urllib.parse import unquote
from dotenv import load_dotenv
from flask_cors import CORS
import drive
import regexes
from pymongo import MongoClient
from models.file import File

load_dotenv(".env")

MODE = "dev"
# MODE = os.getenv("MODE")

USERNAME = os.getenv("MONGO_INITDB_ROOT_USERNAME")
PASSWORD = os.getenv("MONGO_INITDB_ROOT_PASSWORD")
MONGO_PORT = os.getenv("MONGO_PORT")

client = MongoClient(f"mongodb://{USERNAME}:{PASSWORD}@localhost:{MONGO_PORT}/")
db = client.gshare

app = Flask(__name__)
if MODE == "dev":
    cors = CORS(
        app,
        allow_headers=[
            "Cookie",
            "Content-Type",
            "Access-Control-Allow-Credentials",
            "X-User-Email",
        ],
        supports_credentials=True,
        resources={r"*": {"origins": "http://localhost:3000"}},
    )


@app.route("/get-service-accounts", methods=["GET"])
def get_service_accounts(show_rt: bool = False):
    service_accounts = [
        account
        for account in db["service_accounts"].find(
            {},
            {"_id": False, "refresh_token": show_rt, "replicas.refresh_token": show_rt},
        )
    ]
    print(f"{service_accounts = }")
    return service_accounts, 200


@app.route("/auth", methods=["GET"])
def get_auth_link():
    return drive.generate_auth_link(redirect_uri=os.getenv("REDIRECT_URI")), 200


@app.route("/auth", methods=["POST"])
def post_auth_link():
    """Authenticate user with code recieved from google

    Returns:
        user_info: { displayName, picture, email }
    """
    code = unquote(regexes.re_code.findall(request.json["url"])[0])
    creds, user_info = drive.exchange(code)

    db_service.write_creds_by_user_email(user_info["email"], creds.refresh_token)

    return user_info, 200


@app.route("/files", methods={"GET"})
def get_all_files():
    files = drive.get_all_files()
    files = [File(file) for file in files]
    user_email = request.headers["X-User-Email"]
    user_files = drive.get_user_files(user_email)
    return {"files": files, "userFiles": user_files}, 200


@app.route("/")
def hello_world():
    # print(request.data)
    return "works", 200
