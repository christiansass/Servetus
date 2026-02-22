"""
Create Witness records from voice captures.

Pairs audio files with SVP prosodic annotations and plain transcripts
into a Witness markdown file following the Servetus schema.
"""

from datetime import datetime
from pathlib import Path

VAULT_ROOT = Path(__file__).resolve().parent.parent.parent
WITNESS_DIR = VAULT_ROOT / "01-witnesses"


def create_witness(
    audio_path: Path,
    svp_path: Path,
    transcription_result,
    speaker: str = "",
) -> Path:
    """
    Create a Witness markdown file linking audio, SVP, and transcript.

    Returns the path to the created witness file.
    """
    now = datetime.now()
    date_iso = now.strftime("%Y-%m-%d")
    time_str = now.strftime("%H%M")
    timestamp_iso = now.astimezone().isoformat()

    # Time envelope from audio
    duration = transcription_result.duration
    time_start = now.strftime("%Y-%m-%dT%H:%M:%S")
    # Approximate end time
    end_time = now  # The recording just finished, so "now" is roughly the end

    record_id = now.strftime("SV-%Y%m%d-%H%M-CST-VOIC")
    slug = f"voice-capture-{time_str}"
    filename = f"{date_iso}--{slug}--witness.md"
    witness_path = WITNESS_DIR / filename

    # Build plain transcript
    plain_text = transcription_result.text

    # Relative paths for Obsidian links
    audio_link = f"audio/{audio_path.name}"
    svp_link = f"svp/{svp_path.name}"

    content = f"""---
servitus:
  schema_version: 1
  record_type: witness
  pipeline_stage: inbox
  status: draft
  intent: capture

identity:
  title: "Voice Capture — {now.strftime('%B %d, %Y %H:%M')}"
  slug: "{slug}"
  record_id: "{record_id}"

time:
  created_at: "{timestamp_iso}"
  timezone: "America/Chicago"
  source_range: "today"
  time_start: "{time_start}"
  duration: "{duration:.1f}s"

voice:
  model: "whisper-{transcription_result.model}"
  language: "{transcription_result.language}"
  language_confidence: {transcription_result.language_probability:.2f}
  segments: {len(transcription_result.segments)}
  speaker: "{speaker}"

artifacts:
  - path: "[[{audio_link}]]"
    type: audio
    device: "desktop-mic"
    coverage: full
  - path: "[[{svp_link}]]"
    type: voice-performance
    derived_from: "[[{audio_link}]]"
    coverage: full

validity: low
artifact_count: 2
device_count: 1

keywords:
  - voice
  - transcription
  - capture

tags:
  - servitus
  - witness
  - voice

radar:
  active: false
---

# Voice Capture — {now.strftime('%B %d, %Y %H:%M')}

## Exhibit Summary

Voice recording captured locally via Servetus voice pipeline.
Transcribed using whisper-{transcription_result.model} (local, offline).
Prosodic analysis encoded in SVP format.

## Time Envelope

- **Start:** {time_start}
- **Duration:** {duration:.1f}s
- **Timezone:** America/Chicago

## Artifacts

### Artifact 1 — Audio (Primary)

- **Type:** audio
- **Device:** desktop-mic
- **Path:** `[[{audio_link}]]`
- **Coverage:** full
- **Format:** WAV, 16kHz

### Artifact 2 — Voice Performance (Derived)

- **Type:** voice-performance (SVP)
- **Path:** `[[{svp_link}]]`
- **Derived from:** `[[{audio_link}]]`
- **Coverage:** full

## Transcript

{plain_text}

## Validity Assessment

| Factor | Value |
|--------|-------|
| Artifact count | 2 (audio + SVP) |
| Device count | 1 |
| Coverage overlap | full |
| Independent sources | no |
| **Validity** | low |

## Chain of Custody

- Audio captured locally via `servetus voice`
- No data sent to external services
- Transcription: whisper-{transcription_result.model} (local)
- Prosodic analysis: servetus-voice/0.1.0 (local)
- All artifacts stored in vault: `01-witnesses/`
"""

    WITNESS_DIR.mkdir(parents=True, exist_ok=True)
    witness_path.write_text(content.strip() + "\n", encoding="utf-8")

    print(f"  Witness created: {witness_path}")
    return witness_path
