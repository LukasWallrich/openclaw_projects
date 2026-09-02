#!/usr/bin/env python3
"""Transcribe every generated sample and score it against the source script.

Each sample reads the same text, so a transcript gives an objective check on
the parts that matter for spoken notes: the acronyms, the two similar decimals,
the article number, and the URL. The score is not a judgement of how pleasant a
voice sounds — that is what the listening page is for — but it catches voices
that mangle terms, and it confirms every file contains real speech.

Usage (from the project directory, with OPENAI_API_KEY in the environment):
    python3 check_pronunciation.py [--force]
"""

import argparse
import json
import mimetypes
import os
import re
import sys
import urllib.request
import uuid
from pathlib import Path

PROJECT = Path(__file__).resolve().parent
RESULTS = PROJECT / "voices.json"
MODEL = "whisper-1"

# Term to check -> accepted spellings in a transcript.
CHECKS = {
    "GPAI": ["gpai", "g p a i", "g.p.a.i", "gpa i", "g pai"],
    "NIST": ["nist", "n i s t", "n.i.s.t"],
    "HEPI": ["hepi", "h e p i", "h.e.p.i"],
    "Article 50": ["article 50", "article fifty"],
    "24.5%": ["24.5", "twenty-four point five", "twenty four point five"],
    "2.45%": ["2.45", "two point four five", "two point forty-five"],
    "URL": ["url", "u r l", "u.r.l"],
}


def transcribe(path):
    boundary = uuid.uuid4().hex
    parts = []
    for name, value in (("model", MODEL), ("response_format", "text"), ("language", "en")):
        parts.append(
            f"--{boundary}\r\nContent-Disposition: form-data; name=\"{name}\"\r\n\r\n{value}\r\n".encode()
        )
    mime = mimetypes.guess_type(path.name)[0] or "audio/mpeg"
    parts.append(
        f"--{boundary}\r\nContent-Disposition: form-data; name=\"file\"; "
        f"filename=\"{path.name}\"\r\nContent-Type: {mime}\r\n\r\n".encode()
        + path.read_bytes()
        + b"\r\n"
    )
    parts.append(f"--{boundary}--\r\n".encode())
    body = b"".join(parts)

    request = urllib.request.Request(
        "https://api.openai.com/v1/audio/transcriptions",
        data=body,
        headers={
            "Authorization": f"Bearer {os.environ['OPENAI_API_KEY']}",
            "Content-Type": f"multipart/form-data; boundary={boundary}",
        },
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=300) as response:
        return response.read().decode().strip()


def score(transcript):
    flat = re.sub(r"\s+", " ", transcript.lower())
    misread = [term for term, spellings in CHECKS.items()
               if not any(spelling in flat for spelling in spellings)]
    return misread


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--force", action="store_true", help="re-transcribe scored samples")
    args = parser.parse_args()

    if not os.environ.get("OPENAI_API_KEY"):
        sys.exit("OPENAI_API_KEY is not set — source ~/.claude/api_keys.env first")

    data = json.loads(RESULTS.read_text())
    for sample in data["samples"]:
        if sample.get("transcript") and not args.force:
            print(f"skip  {sample['slug']}")
            continue
        path = PROJECT / sample["file"]
        transcript = transcribe(path)
        misread = score(transcript)
        sample["transcript"] = transcript
        sample["misread"] = misread
        print(f"{sample['slug']:20s} {len(CHECKS) - len(misread)}/{len(CHECKS)} correct"
              + (f"  missed: {', '.join(misread)}" if misread else ""))

    data["pronunciation_checks"] = list(CHECKS)
    data["transcription_model"] = MODEL
    RESULTS.write_text(json.dumps(data, indent=2) + "\n")


if __name__ == "__main__":
    main()
