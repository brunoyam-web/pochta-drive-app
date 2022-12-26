from __future__ import print_function
import os
from pprint import pprint
import db_service

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import requests

from models.file import File

URL = str
""" Str URL type """

# If modifying these scopes, delete the file token.json.
SCOPES = [
    "https://www.googleapis.com/auth/drive",
    "https://www.googleapis.com/auth/userinfo.profile",
    "https://www.googleapis.com/auth/userinfo.email",
]


def __authorize(refresh_token: str) -> Credentials:
    print(f"{refresh_token = }")
    creds = Credentials.from_authorized_user_info(
        {
            "refresh_token": refresh_token,
            "client_id": os.getenv("CLIENT_ID"),
            "client_secret": os.getenv("CLIENT_SECRET"),
        },
        scopes=SCOPES,
    )
    pprint(vars(creds))
    print("creds.expired", creds.expired)
    print("creds.valid", creds.valid)
    return creds


async def __get_file_list(refresh_token: str, email: str = ""):
    try:
        creds = __authorize(refresh_token)
        print(f"{creds.token = }")
    except Exception as e:
        if creds.expired or not creds.valid:
            creds.refresh(Request())
            if email != "":
                await db_service.write_creds_by_user_email(creds._refresh_token, email)

    service = build("drive", "v3", credentials=creds)

    try:
        results = (
            service.files()
            .list(
                fields="nextPageToken, files(id, name, mimeType, webContentLink, webViewLink)",
            )
            .execute()
        )
        files = results.get("files", [])

        if not files:
            print("No files found.")
            return []

        return files

    except HttpError as error:
        # TODO(developer) - Handle errors from drive API.
        print(f"An error occurred: {error}")


async def get_files_from_service_accounts():
    service_accounts = await db_service.get_service_accounts()
    files = []
    for account in service_accounts:
        f = await __get_file_list(account["refresh_token"])
        print(f"{account['email'] = }: {len(files)}")
        files += f
    return files


async def get_user_files(email: str):
    refresh_token = await db_service.get_rt_by_user_email(email)
    files = await __get_file_list(refresh_token, email)
    files = [File(file) for file in files]
    return files


def generate_auth_link(
    credentials_path: str = "credentials.json",
    redirect_uri: URL = os.getenv("REDIRECT_URI"),
) -> object:
    """Generates auth link for frontend. You must pass correct redirect uri link to make it works.
    Pay close attention to `/` ending the line

    Args:
        `credentials_path` (str, optional): Defaults to `"credentials.json"`.
        `redirect_uri` (URL, optional): Defaults to `"http://localhost:3000/"`.

    Returns:
        object: {"url": auth_url, "state": state}
    """
    flow = InstalledAppFlow.from_client_secrets_file(
        client_secrets_file=credentials_path,
        scopes=SCOPES,
        redirect_uri=redirect_uri,
    )
    auth_url, state = flow.authorization_url(access_type="offline")
    print(f"{auth_url = }")
    print(f"{state = }")
    return {"url": auth_url, "state": state}


def exchange(code: str) -> tuple[Credentials, dict]:
    # info: map<str, str> "refresh_token", "client_id", "client_secret:
    r = requests.post(
        "https://accounts.google.com/o/oauth2/token",
        headers={"content-type": "application/x-www-form-urlencoded"},
        data={
            "code": code,
            "grant_type": "authorization_code",
            "access_type": "offline",
            "client_id": os.getenv("CLIENT_ID"),
            "redirect_uri": os.getenv("REDIRECT_URI"),
            "client_secret": os.getenv("CLIENT_SECRET"),
        },
    )
    try:
        print(r.json().keys())
        # if "refresh_token" in r.json():
        creds = __authorize(refresh_token=r.json()["refresh_token"])
    except Exception as e:
        print(
            "Could not find refresh token. May be user has logined not for the first time"
        )

    try:
        service = build("oauth2", "v2", credentials=creds)
        results = service.userinfo().get().execute()
        user_info = {
            "displayName": results["name"],
            "email": results["email"],
            "picture": results["picture"],
        }
        return creds, user_info
    except Exception as e:
        print(e)
        return {}, {}


async def copy_file_to_system(owner_email: str, file_id: str):
    user_refresh_token = await db_service.get_rt_by_user_email(owner_email)

    creds = __authorize(user_refresh_token)
    service = build("drive", "v3", credentials=creds)

    try:
        permissions = (
            service.permissions()
            .create(fileId=file_id, body={"type": "anyone", "role": "reader"})
            .execute()
        )
    except Exception as e:
        print(e)

    service_accounts = await db_service.get_service_accounts()

    creds = __authorize(service_accounts[0]["refresh_token"])
    service = build("drive", "v3", credentials=creds)
    results = service.files().copy(fileId=file_id).execute()
    new_file_id = results["id"]

    # allow to share this file for others
    permissions = (
        service.permissions()
        .create(fileId=new_file_id, body={"type": "anyone", "role": "reader"})
        .execute()
    )
    return results, permissions


async def make_system_file_public_if_not(file_id: str) -> bool:
    service_accounts = await db_service.get_service_accounts()
    service = None

    for account in service_accounts:
        creds = __authorize(account["refresh_token"])
        service = build("drive", "v3", credentials=creds)
        permissions = None
        try:
            permissions = service.permissions().list(fileId=file_id).execute()
            print(f"{account['email']} IS owner")
            # print(f"{file_id}: {permissions = }")
        except Exception as e:
            print(f"{account['email']} is not owner")
        if permissions is not None:
            owner = account
            break
    if (
        permissions["permissions"][0]["role"] in ["reader", "writer"]
        and permissions["permissions"][0]["type"] == "anyone"
    ):
        return
    permissions = (
        service.permissions()
        .create(fileId=file_id, body={"type": "anyone", "role": "reader"})
        .execute()
    )


async def copy_file_to_user(email: str, file_id: str):
    """Copies file by fileId to user google drive

    Args:
        email (str): user email to get token from db
        fileId (str): google fileId

    Returns:
        results:

        {
            'kind': 'drive#file',
            'id': '1GMbZUbqoNLvXOhrqsDB4UcPPR6UFOiNM',
            'name': 'img.png',
            'mimeType': 'image/jpeg'
        }

    """

    refresh_token = await db_service.get_rt_by_user_email(email=email)
    creds = __authorize(refresh_token)
    service = build("drive", "v3", credentials=creds)
    make_system_file_public_if_not(file_id)

    results = service.files().copy(fileId=file_id).execute()
    new_file_id = results["id"]

    # allow to share this file for others
    permissions = (
        service.permissions()
        .create(fileId=new_file_id, body={"type": "anyone", "role": "reader"})
        .execute()
    )

    new_file = (
        service.files()
        .get(
            fileId=new_file_id,
            fields="id, name, mimeType, webContentLink, webViewLink",
        )
        .execute()
    )
    new_file = File(new_file)

    return results, permissions
