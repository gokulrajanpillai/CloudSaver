import os
import json
import io
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from PIL import Image

# SCOPES = ['https://www.googleapis.com/auth/drive.metadata.readonly']
SCOPES = ['https://www.googleapis.com/auth/drive']
OUTPUT_DIR = "output"
DOWNLOAD_DIR = os.path.join(OUTPUT_DIR, "downloaded")
REDUCED_DIR = os.path.join(OUTPUT_DIR, "reduced")

QUERY_MEDIA_FILES = "(mimeType contains 'image/' or mimeType contains 'video/') and 'me' in owners and trashed = false"
QUERY_ALL_FILES = "'me' in owners and trashed = false"

def human_readable_size(size_bytes):
    # Converts bytes to human-readable format
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.2f} PB"


def regenerate_token_and_credentials():
    flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
    creds = flow.run_local_server(port=0)
    os.remove("token.json") if os.path.exists("token.json") else None
    # Save the credentials for the next run
    with open("token.json", "w") as token:
        token.write(creds.to_json())
        print("🔑 Token regenerated and saved to token.json")
    return creds


def authenticate():
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)
        if not creds or not creds.valid or creds.expired:
            creds = regenerate_token_and_credentials()
    else:
        creds = regenerate_token_and_credentials()
    return build('drive', 'v3', credentials=creds)


def fetch_files(service, query):
    page_token = None
    all_files = []
    count = 0

    print("📦 Scanning Drive for media files (this may take a while)...")
    while True:
        response = (
            service.files()
            .list(
                q=query,
                spaces='drive',
                fields='nextPageToken, files(id, name, mimeType, size, ownedByMe)',
                pageToken=page_token,
            )
            .execute()
        )

        files = response.get('files', [])
        for file in files:
            file_info = {
                "name": file.get('name'),
                "path": f"https://drive.google.com/file/d/{file.get('id')}/view",  # Using sharable path
                "size_bytes": int(file.get('size', 0)),
                "mimeType": file.get('mimeType'),
                "ownedByMe": file.get('ownedByMe'),
            }
            all_files.append(file_info)
            count += 1
            if count % 50 == 0:
                print(f"   ...{count} files scanned")

        page_token = response.get('nextPageToken', None)
        if not page_token:
            break

    if not all_files:
        print("❌ No files matching the query found in Google Drive.")
    else:
        print(f"✅ Found {len(all_files)} files matching the query.\n")
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


def reduce_image_to_1080p(input_path, output_path):
    """
    Reduces the image at input_path to HD 1080p (1920x1080) and saves to output_path.
    Maintains aspect ratio; does not upscale smaller images.
    Prints file name, path, before and after file size.
    """
    before_size = os.path.getsize(input_path)
    with Image.open(input_path) as img:
        max_size = (1920, 1080)
        img.thumbnail(max_size, Image.LANCZOS)
        img.save(output_path)
    after_size = os.path.getsize(output_path)
    print(f"🖼️ Reduced: {os.path.basename(input_path)}")
    print(f"   Path: {output_path}")
    print(f"   Size before: {human_readable_size(before_size)}")
    print(f"   Size after:  {human_readable_size(after_size)}")
    return before_size, after_size


def download_and_reduce_images(service, files, min_size_mb, number_of_files):
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)
    os.makedirs(REDUCED_DIR, exist_ok=True)
    total_bytes_saved = 0
    min_size_bytes = min_size_mb * 1024 * 1024
    image_files = [
        f
        for f in files
        if f.get('mimeType', '').startswith('image/')
        and f.get('size_bytes', 0) > min_size_bytes
        and f.get('ownedByMe') is True
    ]
    if not image_files:
        print("❌ No image files found above the specified size.")
        return
    selected_files = image_files[:number_of_files]
    reduced_paths = []
    for file in selected_files:
        print(f"⬇️ Downloading {file['name']} ({human_readable_size(file['size_bytes'])})")
        print(f"   Google Drive Path: {file['path']}")
        request = service.files().get_media(fileId=file['path'].split('/')[-2])
        fh = io.BytesIO()
        try:
            from googleapiclient.http import MediaIoBaseDownload

            downloader = MediaIoBaseDownload(fh, request)
            done = False
            while not done:
                status, done = downloader.next_chunk()
            fh.seek(0)
            local_path = os.path.join(DOWNLOAD_DIR, file['name'])
            with open(local_path, 'wb') as out_file:
                out_file.write(fh.read())
            print(f"✅ Saved to {local_path}")
            reduced_path = os.path.join(REDUCED_DIR, file['name'])
            try:
                before, after = reduce_image_to_1080p(local_path, reduced_path)
                total_bytes_saved += before - after
                reduced_paths.append((file, reduced_path))
            except Exception as img_err:
                print(f"⚠️ Skipped corrupted image {file['name']}: {img_err}")
                continue
        except Exception as e:
            print(f"❌ Failed to download/reduce {file['name']}: {e}")

    # Optionally ask user to replace files in Google Drive
    if reduced_paths:
        print(
            f"\n💾 After replacement you will have saved: {human_readable_size(total_bytes_saved)}"
        )
        answer = (
            input(
                "❓ Do you want to replace the original files in Google Drive with their reduced versions? [y/N]: "
            )
            .strip()
            .lower()
        )
        if answer == "y":
            for file, reduced_path in reduced_paths:
                try:
                    file_id = file['path'].split('/')[-2]
                    # Move original file to trash
                    service.files().update(fileId=file_id, body={'trashed': True}).execute()
                    print(f"🗑️ Moved original {file['name']} to trash in Google Drive.")
                    # Upload reduced file as a new file
                    from googleapiclient.http import MediaFileUpload

                    media_body = MediaFileUpload(
                        reduced_path, mimetype=file['mimeType'], resumable=True
                    )
                    new_file_metadata = {'name': file['name'], 'mimeType': file['mimeType']}
                    new_file = (
                        service.files()
                        .create(body=new_file_metadata, media_body=media_body)
                        .execute()
                    )
                    print(f"🔄 Uploaded reduced version of {file['name']} to Google Drive.")
                except Exception as e:
                    print(f"❌ Failed to replace {file['name']} in Google Drive: {e}")
        print(f"\n💾 Total space saved: {human_readable_size(total_bytes_saved)}")


def find_duplicates(service, files):
    from collections import defaultdict

    print("🔍 Scanning for duplicate files by name and size...")
    grouped = defaultdict(list)
    for file in files:
        key = (file['name'], file['size_bytes'])
        grouped[key].append(file)

    duplicates_to_delete = []
    total_bytes_savable = 0

    for group in grouped.values():
        if len(group) > 1:
            # Keep the first, mark the rest as duplicates
            duplicates_to_delete.extend(group[1:])
            total_bytes_savable += sum(f['size_bytes'] for f in group[1:])

    if not duplicates_to_delete:
        print("✅ No duplicate files found.")
        return

    print(f"⚠️ Found {len(duplicates_to_delete)} duplicate files.")
    print(f"💾 Estimated space that can be saved: {human_readable_size(total_bytes_savable)}")
    confirm = input("❓ Do you want to move these duplicates to trash? [y/N]: ").strip().lower()
    if confirm == 'y':
        for file in duplicates_to_delete:
            try:
                file_id = file['path'].split('/')[-2]
                service.files().update(fileId=file_id, body={'trashed': True}).execute()
                print(f"🗑️ Trashed duplicate: {file['name']} - {file['path']}")
            except Exception as e:
                print(f"❌ Failed to trash {file['name']}: {e}")
    else:
        print("🚫 No files were deleted.")


def main():
    print("🔐 Authenticating with Google Drive...")
    service = authenticate()
    gdrive_files = []

    while True:
        print("\n🎮 Choose an option:")
        print("1. Export all image/video file info to JSON")
        print("2. Export only files larger than X MB to JSON")
        print("3. Replace first X images above X MB and reduce to 1080p")
        print("4. Find duplicate files by name and size")
        print("5. Exit")

        choice = input("👉 Enter choice [1-5]: ").strip()

        if choice == "1":
            gdrive_files = fetch_files(service, QUERY_MEDIA_FILES)
            export_to_json_file(gdrive_files, "all_media_files.json")

        elif choice == "2":
            threshold_str = input("📏 Enter minimum file size in MB: ").strip()
            try:
                threshold_mb = float(threshold_str)
                threshold_bytes = threshold_mb * 1024 * 1024
                if not gdrive_files:
                    gdrive_files = fetch_files(service, QUERY_ALL_FILES)
                large_files = [f for f in gdrive_files if f['size_bytes'] > threshold_bytes]
                if not large_files:
                    print("❌ No files found above the specified size.")
                else:
                    export_to_json_file(
                        large_files, f"media_files_above_{int(threshold_mb)}MB.json"
                    )
            except ValueError:
                print("❌ Invalid number entered.")

        elif choice == "3":
            number_of_files = 0
            try:
                number_of_files = int(
                    input("🔢 Enter the number of files you want to compress: ").strip()
                )
                threshold_mb = float(input("📏 Enter minimum image file size in MB: ").strip())
                gdrive_files = fetch_files(service, QUERY_MEDIA_FILES)
                download_and_reduce_images(service, gdrive_files, threshold_mb, number_of_files)
            except ValueError:
                print("❌ Invalid number entered.")

        elif choice == "4":
            gdrive_files = fetch_files(service, QUERY_ALL_FILES)
            find_duplicates(service, gdrive_files)

        elif choice == "5":
            print("👋 Exiting.")
            break

        else:
            print("❌ Invalid choice. Try again.")


if __name__ == "__main__":
    main()
