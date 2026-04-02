import os
import json
from io import BytesIO
from google.auth.transport.requests import Request
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
import PyPDF2


def ingest_from_drive(folder_id: str) -> list[dict]:
    """Ingest PDF files from a Google Drive folder."""
    credentials_json = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")

    if not credentials_json:
        raise ValueError("GOOGLE_APPLICATION_CREDENTIALS is not set")

    credentials_dict = json.loads(credentials_json)

    credentials = Credentials.from_service_account_info(
        credentials_dict,
        scopes=["https://www.googleapis.com/auth/drive.readonly"]
    )

    drive = build("drive", "v3", credentials=credentials)

    try:
        # 1. List files within the specified folder
        query = f"'{folder_id}' in parents and trashed = false and mimeType = 'application/pdf'"
        results = drive.files().list(
            q=query,
            fields="files(id, name, mimeType)",
            pageSize=50
        ).execute()

        files = results.get("files", [])
        if not files:
            print("❌ No PDF files found in the folder.")
            return []

        print("📂 PDFs in folder:")
        for file in files:
            print(f"- {file['name']} ({file['id']})")

        # 2. Process each file (download and extract text)
        documents = []
        for file in files:
            file_id = file["id"]
            request = drive.files().get_media(fileId=file_id)
            file_stream = BytesIO()
            downloader = MediaIoBaseDownload(file_stream, request)

            done = False
            while not done:
                _, done = downloader.next_chunk()

            file_stream.seek(0)
            pdf_reader = PyPDF2.PdfReader(file_stream)
            text = "\n".join(page.extract_text() for page in pdf_reader.pages)

            documents.append({
                "name": file["name"],
                "id": file_id,
                "text": text
            })

            print(f"✅ Extracted from {file['name']}")

        return documents

    except Exception as error:
        print(f"🚫 Error fetching files from Drive: {error}")
        return []
