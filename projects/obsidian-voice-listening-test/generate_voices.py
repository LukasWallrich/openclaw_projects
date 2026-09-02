#!/usr/bin/env python3
"""Generate the cross-provider voice comparison samples for the listening test.

One fixed pronunciation script is read by every candidate voice, so the page
compares synthesis quality rather than wording. Each response is validated as
decodable audio before it is written into audio/voices/, transcoded to a small
mono MP3, and recorded in voices.json together with the measured OpenRouter
spend. Re-running only regenerates samples that are missing or invalid.

Usage (from the project directory, with API keys in the environment):
    python3 generate_voices.py [--only SLUG ...] [--force]
"""

import argparse
import base64
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
from pathlib import Path

PROJECT = Path(__file__).resolve().parent
AUDIO_DIR = PROJECT / "audio" / "voices"
RESULTS = PROJECT / "voices.json"
FAILURES = PROJECT / "voices-failures.log"

SCRIPT_TEXT = (
    "Article 50 of the European Union AI Act covers G P A I, or general-purpose "
    "artificial intelligence. The European Commission published its guidance in 2026. "
    "N I S T and H E P I are separate organisations. A 24.5 percent change is not the "
    "same as 2.45 percent. The proposal is voluntary, not mandatory; and a legislative "
    "recommendation is not a law. Check the URL, example dot org slash AI dash policy."
)

# provider, model, voice, accent/character label, price note
MANIFEST = [
    # OpenRouter speech endpoint
    ("kokoro-bf-emma", "openrouter", "hexgrad/kokoro-82m", "bf_emma", "British · female"),
    ("kokoro-bm-george", "openrouter", "hexgrad/kokoro-82m", "bm_george", "British · male"),
    ("kokoro-af-heart", "openrouter", "hexgrad/kokoro-82m", "af_heart", "American · female"),
    ("flux-bree", "openrouter", "deepgram/flux-tts:free", "flux-bree-en", "American · female"),
    ("flux-wes", "openrouter", "deepgram/flux-tts:free", "flux-wes-en", "American · male"),
    ("flux-maeve", "openrouter", "deepgram/flux-tts:free", "flux-maeve-en", "American · female"),
    ("aura2-thalia", "openrouter", "deepgram/aura-2", "aura-2-thalia-en", "American · female"),
    ("aura2-apollo", "openrouter", "deepgram/aura-2", "aura-2-apollo-en", "American · male"),
    ("sesame-csm", "openrouter", "sesame/csm-1b", "alloy", "American · neutral"),
    ("fish-s21", "openrouter", "fish-audio/s2.1-pro-free:free", "alloy", "American · neutral"),
    # OpenAI speech endpoint
    ("openai-mini-fable", "openai", "gpt-4o-mini-tts", "fable", "British · male"),
    ("openai-mini-nova", "openai", "gpt-4o-mini-tts", "nova", "American · female"),
    ("openai-mini-onyx", "openai", "gpt-4o-mini-tts", "onyx", "American · male"),
    ("openai-tts1-fable", "openai", "tts-1", "fable", "British · male"),
    ("openai-tts1-nova", "openai", "tts-1", "nova", "American · female"),
    # Gemini generateContent with an audio response
    ("gemini31-kore", "gemini", "gemini-3.1-flash-tts-preview", "Kore", "American · female"),
    ("gemini31-puck", "gemini", "gemini-3.1-flash-tts-preview", "Puck", "American · male"),
    ("gemini25-kore", "gemini", "gemini-2.5-flash-preview-tts", "Kore", "American · female"),
]

MIN_DURATION = 8.0  # the script takes ~25 s; anything much shorter is truncated


def post(url, payload, headers, timeout=300):
    request = urllib.request.Request(
        url, data=json.dumps(payload).encode(), headers=headers, method="POST"
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return response.status, response.headers.get("content-type", ""), response.read()
    except urllib.error.HTTPError as error:
        return error.code, error.headers.get("content-type", ""), error.read()
    except Exception as error:  # network-level failure
        return -1, "", str(error).encode()


def openrouter_usage():
    """Total credits spent so far, used to price each call by difference."""
    request = urllib.request.Request(
        "https://openrouter.ai/api/v1/credits",
        headers={"Authorization": f"Bearer {os.environ['OPENROUTER_API_KEY']}"},
    )
    with urllib.request.urlopen(request, timeout=60) as response:
        return json.load(response)["data"]["total_usage"]


def fetch(provider, model, voice):
    """Return (raw_bytes, content_type, usage) or raise RuntimeError with the API message."""
    if provider == "openrouter":
        status, ctype, body = post(
            "https://openrouter.ai/api/v1/audio/speech",
            {"model": model, "input": SCRIPT_TEXT, "voice": voice, "response_format": "mp3"},
            {
                "Authorization": f"Bearer {os.environ['OPENROUTER_API_KEY']}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://lukaswallrich.github.io/openclaw_projects/",
                "X-Title": "Obsidian voice listening test",
            },
        )
    elif provider == "openai":
        status, ctype, body = post(
            "https://api.openai.com/v1/audio/speech",
            {"model": model, "input": SCRIPT_TEXT, "voice": voice, "response_format": "mp3"},
            {
                "Authorization": f"Bearer {os.environ['OPENAI_API_KEY']}",
                "Content-Type": "application/json",
            },
        )
    elif provider == "gemini":
        url = (
            f"https://generativelanguage.googleapis.com/v1beta/models/{model}"
            f":generateContent?key={os.environ['GEMINI_API_KEY']}"
        )
        status, ctype, body = post(
            url,
            {
                "contents": [{"parts": [{"text": SCRIPT_TEXT}]}],
                "generationConfig": {
                    "responseModalities": ["AUDIO"],
                    "speechConfig": {
                        "voiceConfig": {"prebuiltVoiceConfig": {"voiceName": voice}}
                    },
                },
            },
            {"Content-Type": "application/json"},
        )
        if status == 200:
            parsed = json.loads(body)
            part = parsed["candidates"][0]["content"]["parts"][0]["inlineData"]
            return (base64.b64decode(part["data"]), part.get("mimeType", ""),
                    parsed.get("usageMetadata"))
    else:
        raise RuntimeError(f"unknown provider {provider}")

    if status != 200:
        raise RuntimeError(f"HTTP {status}: {body[:300].decode('utf-8', 'replace')}")
    return body, ctype, None


def pcm_rate(content_type):
    """Sample rate for a raw L16/PCM response, or None if the payload is a container."""
    lowered = content_type.lower()
    if "l16" in lowered or "pcm" in lowered:
        for field in lowered.split(";"):
            if "rate=" in field:
                return int(field.split("rate=")[1].strip())
        return 24000
    return None


def transcode(raw, content_type, destination):
    """Write a validated 64 kbps mono MP3, or raise RuntimeError."""
    with tempfile.TemporaryDirectory() as tmp:
        source = Path(tmp) / "input"
        source.write_bytes(raw)
        rate = pcm_rate(content_type)
        command = ["ffmpeg", "-v", "error", "-y"]
        if rate:
            command += ["-f", "s16le", "-ar", str(rate), "-ac", "1"]
        command += ["-i", str(source), "-ac", "1", "-ar", "24000", "-b:a", "64k",
                    str(Path(tmp) / "out.mp3")]
        result = subprocess.run(command, capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError(f"ffmpeg rejected the response: {result.stderr.strip()[:200]}")
        duration = probe_duration(Path(tmp) / "out.mp3")
        if duration is None or duration < MIN_DURATION:
            raise RuntimeError(f"decoded audio is {duration}s, below the {MIN_DURATION}s floor")
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(Path(tmp) / "out.mp3", destination)
        return duration


def probe_duration(path):
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "a:0",
         "-show_entries", "format=duration", "-of", "csv=p=0", str(path)],
        capture_output=True, text=True,
    )
    try:
        return round(float(result.stdout.strip()), 2)
    except ValueError:
        return None


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--only", nargs="*", default=None, help="slugs to (re)generate")
    parser.add_argument("--force", action="store_true", help="regenerate even if valid")
    args = parser.parse_args()

    for key in ("OPENROUTER_API_KEY", "OPENAI_API_KEY", "GEMINI_API_KEY"):
        if not os.environ.get(key):
            sys.exit(f"{key} is not set — source ~/.claude/api_keys.env first")

    document, previous = {}, {}
    if RESULTS.exists():
        document = json.loads(RESULTS.read_text())
        previous = {entry["slug"]: entry for entry in document["samples"]}

    results, failures = [], []
    for slug, provider, model, voice, character in MANIFEST:
        if args.only and slug not in args.only:
            if slug in previous:
                results.append(previous[slug])
            continue

        destination = AUDIO_DIR / f"{slug}.mp3"
        duration = probe_duration(destination) if destination.exists() else None
        if duration and duration >= MIN_DURATION and not args.force:
            entry = dict(previous.get(slug, {}))
            entry.update(slug=slug, provider=provider, model=model, voice=voice,
                         character=character, file=f"audio/voices/{slug}.mp3",
                         duration=duration, bytes=destination.stat().st_size)
            results.append(entry)
            print(f"skip  {slug:20s} already valid ({duration}s)")
            continue

        before = openrouter_usage() if provider == "openrouter" else None
        try:
            raw, content_type, usage = fetch(provider, model, voice)
            duration = transcode(raw, content_type, destination)
        except Exception as error:
            failures.append(f"{slug}\t{provider}\t{model}\t{voice}\t{error}")
            print(f"FAIL  {slug:20s} {error}")
            continue
        cost = None
        if before is not None:
            time.sleep(2)  # OpenRouter books usage a moment after the response
            cost = round(openrouter_usage() - before, 6)

        results.append({
            "slug": slug, "provider": provider, "model": model, "voice": voice,
            "character": character, "file": f"audio/voices/{slug}.mp3",
            "duration": duration, "bytes": destination.stat().st_size,
            "measured_cost_usd": cost, "usage": usage,
        })
        print(f"ok    {slug:20s} {duration}s  {destination.stat().st_size} bytes"
              + (f"  ${cost}" if cost is not None else ""))

    # Keep whatever check_pronunciation.py added at the top level.
    document.update({"script": SCRIPT_TEXT, "characters": len(SCRIPT_TEXT), "samples": results})
    RESULTS.write_text(json.dumps(document, indent=2) + "\n")
    FAILURES.write_text("\n".join(failures) + ("\n" if failures else ""))
    print(f"\n{len(results)} samples in {RESULTS.name}, {len(failures)} failures in {FAILURES.name}")


if __name__ == "__main__":
    main()
