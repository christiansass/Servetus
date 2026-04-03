#!/usr/bin/env python3
"""
attachment-handler.py — File attachment processing for Servetus Talk bot.

Called by talk-webhook.py when a message contains a file attachment.

Supported types:
  PDF          → pdftotext → plain text
  DOCX/ODT     → python-docx → plain text
  TXT/MD/CSV   → read directly
  Images       → base64-encoded for Claude vision (jpg, png, gif, webp)
  Audio/Video  → local Whisper transcription (webm, mp3, wav, m4a, ogg)

Returns a ProcessedAttachment with:
  .text        → extracted text content (or transcription)
  .image_data  → base64 image bytes for Claude vision (None if not image)
  .media_type  → MIME type string for Claude vision block
  .filename    → original filename
  .summary     → one-line human description of what was processed

NC WebDAV download path:
  GET /remote.php/dav/files/<user>/Talk/<filename>
"""

import base64
import json
import subprocess
import tempfile
import urllib.request
import urllib.parse
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

VAULT_ROOT   = Path(__file__).parent.parent
ATTACHMENTS  = VAULT_ROOT / "10-System" / "attachments"
ATTACHMENTS.mkdir(parents=True, exist_ok=True)

# Whisper model — "base" is fast; upgrade to "small" or "medium" for accuracy
WHISPER_MODEL = "base"

# MIME type routing
PDF_TYPES   = {"application/pdf"}
DOCX_TYPES  = {
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/msword",
    "application/vnd.oasis.opendocument.text",
}
TEXT_TYPES  = {"text/plain", "text/markdown", "text/csv", "application/json"}
IMAGE_TYPES = {"image/jpeg", "image/png", "image/gif", "image/webp"}
AUDIO_TYPES = {
    "audio/webm", "video/webm", "audio/mpeg", "audio/mp3",
    "audio/wav", "audio/x-wav", "audio/mp4", "audio/m4a",
    "audio/ogg", "video/mp4",
}


@dataclass
class ProcessedAttachment:
    filename: str
    text: Optional[str]          # Extracted or transcribed text
    image_data: Optional[bytes]  # Raw bytes for Claude vision (images only)
    media_type: Optional[str]    # MIME for Claude vision block
    summary: str                 # Human-readable description

    def to_claude_content(self) -> list:
        """
        Build Claude API content blocks for this attachment.
        Returns a list of content blocks to prepend to the user message.
        """
        blocks = []
        if self.image_data and self.media_type:
            blocks.append({
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": self.media_type,
                    "data": base64.b64encode(self.image_data).decode(),
                }
            })
        if self.text:
            blocks.append({
                "type": "text",
                "text": f"[Attachment: {self.filename}]\n\n{self.text}"
            })
        return blocks


# ── Download ──────────────────────────────────────────────────────────────────

def download_attachment(nc_url: str, nc_user: str, nc_password: str,
                        file_path: str, filename: str) -> Path:
    """
    Download a file from NC Talk folder via WebDAV.
    Returns local path to saved file.
    """
    dest = ATTACHMENTS / filename
    if dest.exists():
        return dest  # Already downloaded this session

    encoded = urllib.parse.quote(file_path)
    dav_url = f"{nc_url}/remote.php/dav/files/{nc_user}/{encoded}"
    b64     = base64.b64encode(f"{nc_user}:{nc_password}".encode()).decode()
    req     = urllib.request.Request(dav_url, headers={"Authorization": f"Basic {b64}"})
    with urllib.request.urlopen(req, timeout=30) as r:
        dest.write_bytes(r.read())

    return dest


# ── Text Extraction ────────────────────────────────────────────────────────────

def extract_pdf(path: Path) -> str:
    result = subprocess.run(
        ["pdftotext", str(path), "-"],
        capture_output=True, text=True, timeout=30
    )
    text = result.stdout.strip()
    if not text:
        raise ValueError("pdftotext returned empty output")
    return text


def extract_docx(path: Path) -> str:
    import docx as python_docx
    doc  = python_docx.Document(str(path))
    return "\n".join(p.text for p in doc.paragraphs if p.text.strip())


def extract_text_file(path: Path) -> str:
    return path.read_text(errors="replace").strip()


# ── Transcription ─────────────────────────────────────────────────────────────

_whisper_model = None

def get_whisper_model():
    global _whisper_model
    if _whisper_model is None:
        import whisper
        print(f"[attachment] Loading Whisper model '{WHISPER_MODEL}'...")
        _whisper_model = whisper.load_model(WHISPER_MODEL)
        print("[attachment] Whisper model ready")
    return _whisper_model


def transcribe_audio(path: Path) -> str:
    """Convert to WAV if needed, then transcribe with local Whisper."""
    audio_path = path

    # Convert non-WAV formats to WAV for Whisper compatibility
    if path.suffix.lower() not in (".wav",):
        wav_path = path.with_suffix(".wav")
        if not wav_path.exists():
            subprocess.run(
                ["ffmpeg", "-y", "-i", str(path), "-ar", "16000", "-ac", "1",
                 "-f", "wav", str(wav_path)],
                capture_output=True, check=True, timeout=120
            )
        audio_path = wav_path

    model  = get_whisper_model()
    result = model.transcribe(str(audio_path))
    return result["text"].strip()


def transcribe_via_nc(nc_url: str, nc_user: str, nc_password: str,
                      file_id: str) -> Optional[str]:
    """
    Submit async transcription job to NC Assistant API (core:audio2text).
    Returns transcribed text or None if unavailable.
    This is a synchronous poll — max ~60s wait.
    """
    b64  = base64.b64encode(f"{nc_user}:{nc_password}".encode()).decode()
    h    = {"Authorization": f"Basic {b64}", "OCS-APIREQUEST": "true",
            "Content-Type": "application/json"}

    # Submit task
    payload = json.dumps({
        "type":  "core:audio2text",
        "appId": "servetus",
        "input": {"input": int(file_id)},
    }).encode()
    req = urllib.request.Request(
        f"{nc_url}/ocs/v2.php/apps/assistant/api/v1/task?format=json",
        data=payload, headers=h, method="POST"
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            data    = json.loads(r.read())
            task_id = data["ocs"]["data"]["task"]["id"]
    except Exception as e:
        print(f"[attachment] NC transcription submit failed: {e}")
        return None

    # Poll for completion (max 60s)
    import time
    for _ in range(12):
        time.sleep(5)
        poll = urllib.request.Request(
            f"{nc_url}/ocs/v2.php/apps/assistant/api/v1/task/{task_id}?format=json",
            headers=h
        )
        try:
            with urllib.request.urlopen(poll, timeout=15) as r:
                d      = json.loads(r.read())
                task   = d["ocs"]["data"]["task"]
                status = task.get("status")
                if status == 4:  # STATUS_SUCCESSFUL
                    return task.get("output", {}).get("output", "").strip()
                if status in (3, 5):  # STATUS_FAILED or STATUS_CANCELLED
                    return None
        except Exception:
            continue

    return None


# ── Main Entry Point ──────────────────────────────────────────────────────────

def process_attachment(file_info: dict, nc_url: str, nc_user: str,
                       nc_password: str) -> Optional[ProcessedAttachment]:
    """
    Given a NC Talk messageParameters['file'] dict, download and process the attachment.

    file_info keys: name, path, mimetype, id, size
    Returns ProcessedAttachment or None on failure.
    """
    filename = file_info.get("name", "unknown")
    nc_path  = file_info.get("path", "")       # e.g. "Talk/Resume JNC 260308.pdf"
    mimetype = file_info.get("mimetype", "")
    file_id  = file_info.get("id", "")
    size_str = file_info.get("size", "0")
    size     = int(size_str) if str(size_str).isdigit() else 0

    # Hard size limit: skip files > 50MB
    if size > 50 * 1024 * 1024:
        print(f"[attachment] {filename}: too large ({size} bytes) — skipping")
        return None

    print(f"[attachment] Processing: {filename} ({mimetype}, {size} bytes)")

    try:
        local_path = download_attachment(nc_url, nc_user, nc_password, nc_path, filename)
    except Exception as e:
        print(f"[attachment] Download failed: {e}")
        return None

    # ── Images ────────────────────────────────────────────────────────────────
    if mimetype in IMAGE_TYPES:
        image_data = local_path.read_bytes()
        return ProcessedAttachment(
            filename=filename,
            text=None,
            image_data=image_data,
            media_type=mimetype,
            summary=f"Image shared: {filename}",
        )

    # ── PDF ───────────────────────────────────────────────────────────────────
    if mimetype in PDF_TYPES:
        try:
            text = extract_pdf(local_path)
            return ProcessedAttachment(
                filename=filename,
                text=text,
                image_data=None,
                media_type=None,
                summary=f"PDF: {filename} ({len(text.split())} words extracted)",
            )
        except Exception as e:
            print(f"[attachment] PDF extraction failed: {e}")
            return None

    # ── DOCX / ODT ────────────────────────────────────────────────────────────
    if mimetype in DOCX_TYPES:
        try:
            text = extract_docx(local_path)
            return ProcessedAttachment(
                filename=filename,
                text=text,
                image_data=None,
                media_type=None,
                summary=f"Document: {filename} ({len(text.split())} words extracted)",
            )
        except Exception as e:
            print(f"[attachment] DOCX extraction failed: {e}")
            return None

    # ── Plain text ────────────────────────────────────────────────────────────
    if mimetype in TEXT_TYPES or local_path.suffix.lower() in (".txt", ".md", ".csv"):
        try:
            text = extract_text_file(local_path)
            return ProcessedAttachment(
                filename=filename,
                text=text,
                image_data=None,
                media_type=None,
                summary=f"Text file: {filename}",
            )
        except Exception as e:
            print(f"[attachment] Text read failed: {e}")
            return None

    # ── Audio / Video ─────────────────────────────────────────────────────────
    if mimetype in AUDIO_TYPES or local_path.suffix.lower() in (
        ".webm", ".mp3", ".wav", ".m4a", ".ogg", ".mp4"
    ):
        # Try local Whisper first — faster for files already downloaded
        try:
            print(f"[attachment] Transcribing via local Whisper: {filename}")
            text = transcribe_audio(local_path)
            if text:
                return ProcessedAttachment(
                    filename=filename,
                    text=f"[Transcription of {filename}]\n\n{text}",
                    image_data=None,
                    media_type=None,
                    summary=f"Audio transcribed: {filename} ({len(text.split())} words)",
                )
        except Exception as e:
            print(f"[attachment] Local Whisper failed: {e} — trying NC API")

        # Fallback: NC server-side transcription
        if file_id and nc_url:
            try:
                text = transcribe_via_nc(nc_url, nc_user, nc_password, file_id)
                if text:
                    return ProcessedAttachment(
                        filename=filename,
                        text=f"[Transcription of {filename}]\n\n{text}",
                        image_data=None,
                        media_type=None,
                        summary=f"Audio transcribed via NC: {filename}",
                    )
            except Exception as e:
                print(f"[attachment] NC transcription failed: {e}")

        print(f"[attachment] Transcription failed for {filename}")
        return None

    print(f"[attachment] Unsupported type: {mimetype} ({filename})")
    return None
