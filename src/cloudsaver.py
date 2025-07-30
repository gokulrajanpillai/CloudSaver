import os
import json
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = ['https://www.googleapis.com/auth/drive.metadata.readonly']
OUTPUT_DIR = "output"

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
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_in_bytes < 1024:
            return f"{size_in_bytes:.2f} {unit}"
        size_in_bytes /= 1024
    return f"{size_in_bytes:.2f} PB"


def fetch_media_files(service):
    query = "mimeType contains 'image/' or mimeType contains 'video/'"
    page_token = None
    all_files = []
    count = 0

    print("📦 Scanning Drive for media files (this may take a while)...")
    while True:
        response = service.files().list(
            q=query,
            spaces='drive',
            fields='nextPageToken, files(id, name, mimeType, size)',
            pageToken=page_token
        ).execute()

        files = response.get('files', [])
        for file in files:
            file_info = {
                "name": file.get('name'),
                "path": f"https://drive.google.com/file/d/{file.get('id')}/view",  # Using sharable path
                "size_bytes": int(file.get('size', 0)),
                "mimeType": file.get('mimeType')
            }
            all_files.append(file_info)
            count += 1
            if count % 50 == 0:
                print(f"   ...{count} files scanned")

        page_token = response.get('nextPageToken', None)
        if not page_token:
            break

    print(f"✅ Found {len(all_files)} media files.\n")
    return all_files


def export_to_json_file(data, filename):
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    filename = os.path.join(OUTPUT_DIR, filename)
    if not data:
        print("❌ No data to export.")
        return
    with open(filename, "w") as f:
        json.dump(data, f, indent=2)
    print(f"✅ JSON saved to {filename}")


def main():
    print("🔐 Authenticating with Google Drive...")
    service = authenticate()
    media_files = []

    while True:
        print("\n🎮 Choose an option:")
        print("1. Export all image/video file info to JSON")
        print("2. Export only files larger than X MB to JSON")
        print("3. Exit")

        choice = input("👉 Enter choice [1-3]: ").strip()

        if choice == "1":
            media_files = fetch_media_files(service)
            export_to_json_file(media_files, "all_media_files.json")

        elif choice == "2":
            threshold_str = input("📏 Enter minimum file size in MB: ").strip()
            try:
                threshold_mb = float(threshold_str)
                threshold_bytes = threshold_mb * 1024 * 1024
                if not media_files:
                    media_files = fetch_media_files(service)
                large_files = [f for f in media_files if f['size_bytes'] > threshold_bytes]
                export_to_json_file(large_files, f"media_files_above_{int(threshold_mb)}MB.json")
            except ValueError:
                print("❌ Invalid number entered.")

        elif choice == "3":
            print("👋 Exiting.")
            break

        else:
            print("❌ Invalid choice. Try again.")


if __name__ == "__main__":
    main()
