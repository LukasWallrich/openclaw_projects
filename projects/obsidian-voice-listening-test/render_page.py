#!/usr/bin/env python3
"""Render the cross-provider lab from voices.json into index.html.

The page keeps hand-written prose; everything between the VOICE-LAB markers is
generated, so re-running after a new sample run refreshes players, durations,
pronunciation scores, and costs without touching the rest of the page.

Usage (from the project directory):
    python3 render_page.py
"""

import html
import json
from pathlib import Path

PROJECT = Path(__file__).resolve().parent
RESULTS = PROJECT / "voices.json"
PAGE = PROJECT / "index.html"
START = "<!-- VOICE-LAB:START -->"
END = "<!-- VOICE-LAB:END -->"

BRIEF_CHARACTERS = 5900  # a 1,000-word spoken brief

# The OpenAI speech endpoint returns no usage figures. This rate comes from a
# gpt-audio-mini call that reported 190 audio tokens for 9.6 seconds of speech;
# both models bill against the same $12 / 1M audio-token meter.
OPENAI_AUDIO_TOKENS_PER_SECOND = 190 / 9.6

# model -> (display name, link, price note, cost of one 1,000-word brief)
# Character prices are OpenRouter endpoint prices; OpenAI and Google prices are
# from their own pricing pages. Gemini bills audio output by token, so its brief
# cost is scaled from the tokens-per-second measured in these samples.
PRICING = {
    "hexgrad/kokoro-82m": {
        "name": "Kokoro 82M",
        "link": "https://openrouter.ai/hexgrad/kokoro-82m",
        "route": "OpenRouter → DeepInfra",
        "price": "$0.62 / 1M characters",
        "per_million_characters": 0.62,
    },
    "deepgram/flux-tts:free": {
        "name": "Deepgram Flux TTS",
        "link": "https://openrouter.ai/deepgram/flux-tts:free",
        "route": "OpenRouter free tier",
        "price": "free",
        "per_million_characters": 0.0,
    },
    "deepgram/aura-2": {
        "name": "Deepgram Aura-2",
        "link": "https://openrouter.ai/deepgram/aura-2",
        "route": "OpenRouter → Deepgram",
        "price": "$30 / 1M characters",
        "per_million_characters": 30.0,
    },
    "fish-audio/s2.1-pro-free:free": {
        "name": "Fish Audio S2.1 Pro",
        "link": "https://openrouter.ai/fish-audio/s2.1-pro-free:free",
        "route": "OpenRouter free tier",
        "price": "free",
        "per_million_characters": 0.0,
    },
    "sesame/csm-1b": {
        "name": "Sesame CSM 1B",
        "link": "https://openrouter.ai/sesame/csm-1b",
        "route": "OpenRouter → DeepInfra",
        "price": "$7 / 1M characters",
        "per_million_characters": 7.0,
    },
    "tts-1": {
        "name": "OpenAI TTS-1",
        "link": "https://developers.openai.com/api/docs/pricing",
        "route": "OpenAI API",
        "price": "$15 / 1M characters",
        "per_million_characters": 15.0,
    },
    "gpt-4o-mini-tts": {
        "name": "OpenAI GPT-4o mini TTS",
        "link": "https://developers.openai.com/api/docs/pricing",
        "route": "OpenAI API",
        "price": "$0.60 / 1M input characters + $12 / 1M audio tokens",
        "per_million_characters": 0.60,
        "per_million_audio_tokens": 12.0,
        "audio_tokens_per_second": OPENAI_AUDIO_TOKENS_PER_SECOND,
        "cost_note": "OpenAI publishes no tokens-per-second figure for speech, so the audio "
                     "half is priced at the 19.8 tokens per second measured from a "
                     "gpt-audio-mini call, which bills on the same audio-token meter. That "
                     "works out at $0.014 per minute.",
    },
    "gemini-3.1-flash-tts-preview": {
        "name": "Gemini 3.1 Flash TTS",
        "link": "https://ai.google.dev/gemini-api/docs/pricing",
        "route": "Gemini API",
        "price": "$1 / 1M input tokens + $20 / 1M audio tokens",
        "per_million_audio_tokens": 20.0,
    },
    "gemini-2.5-flash-preview-tts": {
        "name": "Gemini 2.5 Flash TTS",
        "link": "https://ai.google.dev/gemini-api/docs/pricing",
        "route": "Gemini API",
        "price": "$0.50 / 1M input tokens + $10 / 1M audio tokens",
        "per_million_audio_tokens": 10.0,
    },
}


def brief_cost(model, samples, characters):
    """Cost of one 1,000-word spoken brief, or None when it cannot be derived.

    Models that bill audio output by token are priced from how long these
    samples actually run, so the estimate uses each model's own speaking rate.
    """
    entry = PRICING[model]
    cost = (entry.get("per_million_characters") or 0.0) * BRIEF_CHARACTERS / 1e6
    if entry.get("per_million_audio_tokens") is None:
        return cost if entry.get("per_million_characters") is not None else None

    tokens_per_second = entry.get("audio_tokens_per_second")
    if tokens_per_second is None:
        rates = [s["usage"]["candidatesTokenCount"] / s["duration"]
                 for s in samples if s.get("usage") and s.get("duration")]
        if not rates:
            return None
        tokens_per_second = sum(rates) / len(rates)
    seconds_per_character = sum(s["duration"] for s in samples) / (len(samples) * characters)
    tokens = tokens_per_second * seconds_per_character * BRIEF_CHARACTERS
    return cost + entry["per_million_audio_tokens"] * tokens / 1e6


def money(value):
    if value is None:
        return "—"
    if value == 0:
        return "free"
    return f"${value:.3f}" if value >= 0.001 else "<$0.001"


def render(data):
    samples = data["samples"]
    characters = data["characters"]
    total_checks = len(data["pronunciation_checks"])
    by_model = {}
    for sample in samples:
        by_model.setdefault(sample["model"], []).append(sample)

    rows = []
    cards = []
    for model, group in by_model.items():
        entry = PRICING[model]
        cost = brief_cost(model, group, characters)
        misses = sorted({term for s in group for term in s["misread"]})
        rows.append(
            f'<tr><td><a href="{entry["link"]}">{html.escape(entry["name"])}</a>'
            f'<div class="small">{html.escape(entry["route"])}</div></td>'
            f'<td>{html.escape(entry["price"])}</td>'
            f'<td class="num">{money(cost)}</td>'
            f'<td>{len(group)}</td>'
            f'<td>{"clean" if not misses else html.escape(", ".join(misses))}</td></tr>'
        )
        voice_cards = []
        for sample in sorted(group, key=lambda s: s["slug"]):
            correct = total_checks - len(sample["misread"])
            state = "" if not sample["misread"] else " pending"
            detail = ("all checked terms read correctly" if not sample["misread"]
                      else "missed " + ", ".join(sample["misread"]))
            voice_cards.append(
                '<section class="pronunciation-card">'
                f'<h3>{html.escape(sample["voice"])}</h3>'
                f'<p class="voice-note">{html.escape(sample["character"])} · '
                f'{sample["duration"]:.0f} s</p>'
                f'<audio controls preload="none" src="{sample["file"]}"></audio>'
                f'<div class="status{state}">{correct}/{total_checks} terms · '
                f'{html.escape(detail)}</div>'
                f'<details><summary>transcript</summary><p class="transcript">'
                f'{html.escape(sample["transcript"])}</p></details>'
                "</section>"
            )
        cards.append(
            '<section class="lab">'
            f'<h2>{html.escape(entry["name"])} '
            f'<span class="small">· {html.escape(entry["price"])}</span></h2>'
            f'<p class="lab-intro">{html.escape(entry["route"])} · '
            f'one 1,000-word brief costs {money(cost)}'
            + (f'. {html.escape(entry["cost_note"])}' if entry.get("cost_note") else "")
            + "</p>"
            f'<div class="pronunciation-grid">{"".join(voice_cards)}</div>'
            "</section>"
        )

    failures = (PROJECT / "voices-failures.log").read_text().strip().splitlines()
    failure_html = ""
    if failures:
        items = []
        for line in failures:
            slug, _provider, model, voice, reason = line.split("\t", 4)
            items.append(f"<li><strong>{html.escape(model)}</strong> ({html.escape(voice)}): "
                         f"{html.escape(reason)}</li>")
        failure_html = ('<section class="lab"><h2>Did not produce a sample</h2>'
                        f'<ul class="fail-list">{"".join(items)}</ul></section>')

    table = (
        '<section class="lab"><h2>Cost and pronunciation at a glance</h2>'
        '<p class="lab-intro">Brief cost assumes a 1,000-word spoken summary '
        f'({BRIEF_CHARACTERS:,} characters, about six minutes). Pronunciation is scored by '
        f'transcribing each sample with {html.escape(data["transcription_model"])} and checking '
        f'{total_checks} terms: {html.escape(", ".join(data["pronunciation_checks"]))}.</p>'
        '<div class="table-wrap"><table><thead><tr><th>Model</th><th>List price</th>'
        '<th class="num">Per brief</th><th>Voices</th><th>Terms missed</th></tr></thead>'
        f'<tbody>{"".join(rows)}</tbody></table></div></section>'
    )

    return "\n".join([table] + cards + ([failure_html] if failure_html else []))


def main():
    data = json.loads(RESULTS.read_text())
    page = PAGE.read_text()
    before, _, rest = page.partition(START)
    _, _, after = rest.partition(END)
    if not rest or not after:
        raise SystemExit(f"index.html is missing the {START} / {END} markers")
    PAGE.write_text(before + START + "\n" + render(data) + "\n" + END + after)
    print(f"rendered {len(data['samples'])} samples into index.html")


if __name__ == "__main__":
    main()
