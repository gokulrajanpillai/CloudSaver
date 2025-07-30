import os
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = ['https://www.googleapis.com/auth/drive.metadata.readonly']

def authenticate():
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)
    else:
        flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
        creds = flow.run_local_server(port=0)
        with open("token.json", "w") as token:
            token.write(creds.to_json())
    return build('drive', 'v3', credentials=creds)

def human_readable_size(size_in_bytes):
    if not size_in_bytes:
        return "Unknown"
    size_in_bytes = int(size_in_bytes)
    for unit in ['B','KB','MB','GB','TB']:
        if size_in_bytes < 1024:
            return f"{size_in_bytes:.2f} {unit}"
        size_in_bytes /= 1024
    return f"{size_in_bytes:.2f} PB"

def list_media_files(service):
    query = "mimeType contains 'image/' or mimeType contains 'video/'"
    page_token = None
    while True:
        response = service.files().list(
            q=query,
            spaces='drive',
            fields='nextPageToken, files(id, name, mimeType, size)',
            pageToken=page_token
        ).execute()

        files = response.get('files', [])
        for file in files:
            name = file.get('name')
            mime = file.get('mimeType')
            size = human_readable_size(file.get('size'))
            print(f"📄 {name} | {mime} | {size}")

        page_token = response.get('nextPageToken', None)
        if not page_token:
            break

def main():
    print("🔐 Authenticating with Google Drive...")
    service = authenticate()
    print("📸 Listing all image and video files...\n")
    list_media_files(service)

if __name__ == "__main__":
    main()
