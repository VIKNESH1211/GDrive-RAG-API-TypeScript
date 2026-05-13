import io
import json
import logging
import os
import re

import pdfplumber
import requests
from bs4 import BeautifulSoup
from docx import Document
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload

logger = logging.getLogger(__name__)

_DRIVE_MIMETYPES = (
    "mimeType='application/pdf'"
    " or mimeType='application/vnd.openxmlformats-officedocument.wordprocessingml.document'"
    " or mimeType='text/plain'"
    " or mimeType='text/markdown'"
)


def _drive_service():
    raw = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "{}")
    creds_data = json.loads(raw) if isinstance(raw, str) else raw
    creds = Credentials.from_service_account_info(
        creds_data,
        scopes=["https://www.googleapis.com/auth/drive.readonly"],
    )
    return build("drive", "v3", credentials=creds, cache_discovery=False)


def ingest_from_drive(folder_id: str) -> list[dict]:
    svc = _drive_service()
    result = svc.files().list(
        q=f"'{folder_id}' in parents and trashed=false and ({_DRIVE_MIMETYPES})",
        fields="files(id, name, mimeType)",
        pageSize=100,
    ).execute()

    files = result.get("files", [])
    logger.info("Found %d files in Drive folder %s", len(files), folder_id)

    docs = []
    for f in files:
        try:
            buf = io.BytesIO()
            downloader = MediaIoBaseDownload(buf, svc.files().get_media(fileId=f["id"]))
            done = False
            while not done:
                _, done = downloader.next_chunk()
            buf.seek(0)
            raw_bytes = buf.read()

            mime = f["mimeType"]
            if mime == "application/pdf":
                text = ingest_pdf_bytes(raw_bytes)
            elif "wordprocessingml" in mime:
                text = ingest_docx_bytes(raw_bytes)
            else:
                text = raw_bytes.decode("utf-8", errors="ignore")

            if text.strip():
                docs.append({"name": f["name"], "id": f["id"], "text": text})
                logger.info("Ingested '%s' (%d chars)", f["name"], len(text))
        except Exception as exc:
            logger.error("Failed to ingest '%s': %s", f["name"], exc)

    return docs


def ingest_pdf_bytes(content: bytes) -> str:
    pages = []
    with pdfplumber.open(io.BytesIO(content)) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                pages.append(text)
    return "\n\n".join(pages)


def ingest_docx_bytes(content: bytes) -> str:
    doc = Document(io.BytesIO(content))
    paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
    return "\n\n".join(paragraphs)


def ingest_url(url: str) -> str:
    headers = {"User-Agent": "Mozilla/5.0 (compatible; RAGBot/2.0)"}
    resp = requests.get(url, headers=headers, timeout=30)
    resp.raise_for_status()

    soup = BeautifulSoup(resp.content, "lxml")
    for tag in soup(["script", "style", "nav", "footer", "header", "aside"]):
        tag.decompose()

    main = soup.find("main") or soup.find("article") or soup.find("body")
    text = (main or soup).get_text(separator="\n", strip=True)
    return re.sub(r"\n{3,}", "\n\n", text).strip()
