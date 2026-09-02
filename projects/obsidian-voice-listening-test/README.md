# Obsidian voice listening test

A listening page for picking the text-to-speech voice that will read spoken note
summaries in the Obsidian bridge. It holds three things:

- **Cross-provider lab** — 17 voices from 9 models reading one identical
  stress-test script, with the cost of a 1,000-word brief and a machine-checked
  pronunciation score for each.
- **Kokoro local fixtures** — the same script and four acronym spellings rendered
  on the box with the Kokoro ONNX weights, at no per-character cost.
- **Note pairs** — five short AI-policy notes in two rewrite styles each, for
  choosing a script style rather than a voice. These are 25–28 second excerpts,
  not the 3–5 minute production summaries.

All audio is 64 kbps mono MP3 so the page stays usable on a phone.

## Regenerating

```sh
set -a; source ~/.claude/api_keys.env; set +a
python3 generate_voices.py       # hosted voices → audio/voices/ + voices.json
python3 check_pronunciation.py   # transcribe each sample, score seven terms
python3 render_page.py           # rebuild the lab section of index.html
```

`generate_voices.py` validates every response as decodable audio before it
touches `audio/`; anything that fails is recorded in `voices-failures.log`
instead. All three scripts skip finished work, so a re-run only fills gaps.
Pass `--force` to redo a sample, or `--only <slug>` to work on one.

The local Kokoro fixtures come from `node generate_kokoro.mjs` after
`npm install kokoro-js`; it reads its transcripts out of `index.html`.

## What the samples show

Prices are OpenRouter endpoint rates for the hosted open models and the
providers' own rates for OpenAI and Google. A 1,000-word brief (about six
minutes of speech) costs nothing on the Deepgram Flux and Fish Audio free tiers,
$0.004 on Kokoro, $0.09 on OpenAI TTS-1, and $0.12–$0.29 on the Gemini TTS
models. Kokoro run locally costs nothing and needs no network call.

Pronunciation is scored by transcribing each sample with Whisper and checking
seven terms a policy summary must not mangle: GPAI, NIST, HEPI, Article 50,
24.5%, 2.45%, and URL. Every voice reads at least six of the seven. The misses
are near-misses — "HEP" for HEPI, "GPA1" for GPAI — and they differ by model
rather than by voice.

Sesame CSM 1B returns HTTP 400 on the 470-character script although it succeeds
on a 90-character one, so it cannot serve a brief.

## Acronyms in production

Spaces between letters work for the checked `bf_emma` Kokoro fixture. Periods
between letters caused run-on issues, so they should not be the default. Kokoro
exposes no guaranteed "spell this token" switch, so a normalizer can use spaced
letters and let a verifier or a per-voice exception list catch failures:

```js
const spellAcronyms = (text) => text.replace(/\b[A-Z]{2,}\b/g, (token) => [...token].join(" "));
```

For unfamiliar or high-stakes terms, expand on first use: "general-purpose
artificial intelligence, abbreviated G P A I." That survives a voice reading the
letters imperfectly.
