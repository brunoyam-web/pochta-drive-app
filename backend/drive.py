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

URL = str
""" Str URL type """

# If modifying these scopes, delete the file token.json.
SCOPES = [
    "https://www.googleapis.com/auth/drive",
    "https://www.googleapis.com/auth/userinfo.profile",
    "https://www.googleapis.com/auth/userinfo.email",
]

# Another way to get access token
# def __get_access_token(refresh_token: str):
#     r = requests.post(
#         "https://accounts.google.com/o/oauth2/token",
#         headers={"content-type": "application/x-www-form-urlencoded"},
#         data={
#             "grant_type": "refresh_token",
#             "refresh_token": refresh_token,
#             "access_type": "offline",
#             "client_id": os.getenv("CLIENT_ID"),
#             "redirect_uri": os.getenv("REDIRECT_URI"),
#             "client_secret": os.getenv("CLIENT_SECRET"),
#         },
#     )
#     return r.json()["access_token"]


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

    if creds.expired:
        creds.refresh(Request())
    pprint(vars(creds))
    print("creds.expired", creds.expired)
    print("creds.valid", creds.valid)
    return creds


def __get_file_list(refresh_token: str):

    creds = __authorize(refresh_token)
    print(f"{creds.token = }")
    # return {}
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
    creds = __authorize(refresh_token=r.json()["refresh_token"])

    service = build("oauth2", "v2", credentials=creds)
    results = service.userinfo().get().execute()
    user_info = {
        "displayName": results["name"],
        "email": results["email"],
        "picture": results["picture"],
    }

    return creds, user_info


def get_user_files(email: str):
    refresh_token = db_service.get_rt_by_user_email(email)
    files = __get_file_list(refresh_token)
    return files


def get_all_files():
    service_accounts = db_service.get_service_accounts()
    files = []
    for account in service_accounts:
        f = __get_file_list(account["refresh_token"])
        print(f"{account['email'] = }: {len(files)}")
        files += f
    return files


def copy_file_to_system(fileId: str):
    pass


if __name__ == "__main__":
    get_all_files()
