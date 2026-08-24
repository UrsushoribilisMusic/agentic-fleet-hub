#!/usr/bin/env python3
"""TS-12 — upload tech-shorts shareable assets to Google Drive and return public links.

Reuses music-video-tool/drive_token.pickle (scope: drive). Creates a "Tech Shorts"
folder (and a per-job subfolder), uploads files, sets anyone-with-link viewer, and
prints the webViewLink for each.

Usage: python3 drive_store.py "<subfolder name>" <file> [<file> ...]
"""
import pickle, os, sys
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.auth.transport.requests import Request

TOKEN = os.path.expanduser("~/projects/music-video-tool/drive_token.pickle")
ROOT_FOLDER = "Tech Shorts"


def service():
    creds = pickle.load(open(TOKEN, "rb"))
    if creds and getattr(creds, "expired", False) and creds.refresh_token:
        creds.refresh(Request())
    return build("drive", "v3", credentials=creds)


def find_or_create_folder(svc, name, parent=None):
    q = ("name = '%s' and mimeType = 'application/vnd.google-apps.folder' "
         "and trashed = false" % name.replace("'", "\\'"))
    if parent:
        q += " and '%s' in parents" % parent
    r = svc.files().list(q=q, fields="files(id)", pageSize=1).execute()
    if r.get("files"):
        return r["files"][0]["id"]
    meta = {"name": name, "mimeType": "application/vnd.google-apps.folder"}
    if parent:
        meta["parents"] = [parent]
    return svc.files().create(body=meta, fields="id").execute()["id"]


def upload(svc, path, parent):
    name = os.path.basename(path)
    media = MediaFileUpload(path, resumable=True)
    f = svc.files().create(body={"name": name, "parents": [parent]},
                           media_body=media, fields="id, webViewLink").execute()
    svc.permissions().create(fileId=f["id"],
                             body={"type": "anyone", "role": "reader"}).execute()
    return f["webViewLink"]


def main():
    if len(sys.argv) < 3:
        sys.exit("usage: drive_store.py '<subfolder>' <file> [<file> ...]")
    sub_name, files = sys.argv[1], sys.argv[2:]
    svc = service()
    root = find_or_create_folder(svc, ROOT_FOLDER)
    sub = find_or_create_folder(svc, sub_name, root)
    for p in files:
        p = os.path.expanduser(p)
        if not os.path.exists(p):
            print("  MISSING:", p); continue
        print("  %s -> %s" % (os.path.basename(p), upload(svc, p, sub)))


if __name__ == "__main__":
    main()
