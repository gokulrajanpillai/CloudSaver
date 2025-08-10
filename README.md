# CloudSaver
Save cloud costs by reducing picture and video quality of files uploaded to the cloud.
Identifies files with same name and size and moves duplicates to Trash

## Google Drive OAuth Setup

To use CloudSaver with Google Drive, you need to generate an OAuth token:

1. Go to [Google Cloud Console](https://console.cloud.google.com/).
2. Create a new project or select an existing one.
3. Navigate to **APIs & Services > Library** and enable the **Google Drive API**.
4. Go to **APIs & Services > Credentials** and create an **OAuth 2.0 Client ID**.
5. Download the `credentials.json` file provided by Google.
6. Place the `credentials.json` file in the project root directory.

This file is required for authenticating
