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
$0.004 on Kokoro, $0.09 on OpenAI TTS-1, $0.11 on GPT-4o mini TTS, $0.12 on
Gemini 2.5 Flash TTS, $0.18 on Deepgram Aura-2, and $0.29 on Gemini 3.1 Flash
TTS. Kokoro run locally costs nothing and needs no network call.

Models that bill audio output by the token are priced from how fast they
actually speak in these samples. OpenAI's speech endpoint returns no usage
figures, so the audio half of GPT-4o mini TTS uses the 19.8 tokens per second
measured from a `gpt-audio-mini` call on the same audio-token meter — $0.014 a
minute, which matches the figure OpenAI users report. At these speaking rates
GPT-4o mini TTS costs slightly more per brief than the older TTS-1.

Pronunciation is scored by transcribing each sample with Whisper and checking
seven terms a policy summary must not mangle: GPAI, NIST, HEPI, Article 50,
24.5%, 2.45%, and URL. Every voice reads at least six of the seven. The misses
are near-misses — "HEP" for HEPI, "GPA1" for GPAI — and they differ by model
rather than by voice.

Sesame CSM 1B returns HTTP 400 on the full script although it succeeds on a
90-character one, so it cannot serve a brief.

## The free tiers in practice

OpenRouter allows 20 requests a minute and 1,000 a day on `:free` models once an
account has bought credits, so one brief a day is far inside the budget. Length
and speed decide it instead. Deepgram Flux TTS returns HTTP 413 above about
2,000 characters, so a brief needs three or four calls stitched together, and
its latency swings — the same 1,500-character request took 8 seconds once and
195 seconds another time. Fish Audio S2.1 Pro read a 2,796-character passage in
one 37-second call. Kokoro did the same passage in 5.7 seconds for about a tenth
of a cent.

Free capacity is shared and unpriced, so neither latency figure is a promise,
and neither model has a paid endpoint under the same name to fall back to.
Anything sent to a free variant also reaches a provider on its own retention
terms, which matters more for personal notes than for this policy fixture.

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
