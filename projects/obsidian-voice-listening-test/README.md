# Obsidian voice listening test

This fixture contains five short AI-policy notes, each with two rewrite styles, plus pronunciation labs that read fixed stress-test scripts in four voices and four acronym spellings. It is for comparing spoken-summary scripts and synthesis quality before wiring the pipeline into the Obsidian bridge.

The checked-in note audio is deliberately short excerpts (about 25–28 seconds each), not the target 3–5 minute production summaries. The pronunciation tracks use the same text in `bf_emma`, `bm_george`, `af_heart`, and `am_michael`; the acronym tracks hold the voice fixed and vary only the spelling strategy. All local fixtures were generated with Kokoro-82M at 24 kHz mono.

## Regenerate locally

From this directory, install the local runtime and run the generator:

```sh
npm install kokoro-js
node generate_kokoro.mjs
```

The generator uses the same Kokoro ONNX model for every sample. The paired note tracks isolate rewrite style, the pronunciation tracks isolate voice choice, and the acronym tracks test whether spaces, periods, spoken letters, or expansion are most reliable. The page also links to the primary policy sources used for the scripts.

## Acronyms in production

Spaces are a useful first heuristic, but Kokoro does not expose a guaranteed “spell this token” switch. For all-caps tokens, a normalizer can try spaced letters and let the verifier or a per-voice exception list catch failures:

```js
const spellAcronyms = (text) => text.replace(/\b[A-Z]{2,}\b/g, (token) => [...token].join(" "));
```

For unfamiliar or high-stakes terms, expand on first use: “general-purpose artificial intelligence, abbreviated G P A I.” This is more robust than relying on punctuation, and it remains understandable if a voice reads the letters imperfectly.

For an API-backed run, OpenRouter exposes the same model as `hexgrad/kokoro-82m` through its speech endpoint. Keep credentials out of the repository and replace the local fixtures only after checking the resulting files in a browser.
