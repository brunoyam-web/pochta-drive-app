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

# drive.init_db()

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
        resources={
            r"*": {
                "origins": [
                    "*",
                ]
            }
        },
    )


@app.route("/auth", methods=["GET"])
def get_auth_link():
    return drive.generate_auth_link(redirect_uri=os.getenv("REDIRECT_URI")), 200


@app.route("/auth", methods=["POST"])
async def post_auth_link():
    """Authenticate user with code recieved from google

    You should pass object { "url": "code=<GOOGLE_AUTH_CODE>" }

    Returns:
        user_info: { displayName, picture, email }
    """
    code = unquote(regexes.re_code.findall(request.json["url"])[0])

    creds, user_info = drive.exchange(code)

    user_exist = await db_service.user_exists(user_info["email"])

    if user_exist is None:
        await db_service.write_creds_by_user_email(
            user_info["email"], creds.refresh_token
        )

    return user_info, 200


@app.route("/files", methods={"GET"})
async def get_system_files():
    files = await drive.get_files_from_service_accounts()
    files = [File(file) for file in files]
    return files, 200


@app.route("/files/user", methods={"GET"})
async def get_user_files():
    print(request.headers["X-User-Email"])
    if "X-User-Email" in request.headers:
        user_email = request.headers["X-User-Email"]
        user_files = await drive.get_user_files(user_email)
        return user_files, 200
    return [], 500


@app.route("/copy", methods={"POST"})
async def copy_file_to_user():
    """Copies file to user google drive

    Pass Headers: X-User-Email - user email
    """
    if "fileId" in request.json and "X-User-Email" in request.headers:
        email = request.headers["X-User-Email"]
        fileId = request.json["fileId"]
        res, permissions = await drive.copy_file_to_user(email, fileId)
        return {"success": True, "res": res, "permissions": permissions}, 200
    return {"success": False}, 500


@app.route("/share", methods={"POST"})
async def copy_file_to_system():
    """Share user file with others

    Recieves:
    - Headers: X-User-Email
    - Payload: { "fileId": "<FILE_ID>"}

    """
    if "fileId" in request.json and "X-User-Email" in request.headers:
        email = request.headers["X-User-Email"]
        fileId = request.json["fileId"]
        res, permissions = await drive.copy_file_to_system(email, fileId)
        return {"success": True, "res": res, "permissions": permissions}, 200
    return {"success": False}, 500


@app.route("/")
def hello_world():
    return "works", 200
