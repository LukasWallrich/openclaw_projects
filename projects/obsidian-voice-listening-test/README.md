# Obsidian voice listening test

This fixture contains five short AI-policy notes, each with two rewrite styles, for comparing spoken-summary scripts before wiring the pipeline into the Obsidian bridge.

The checked-in audio samples are deliberately short excerpts (about 25–28 seconds each), not the target 3–5 minute production summaries. They were generated with Kokoro-82M, voice `bf_emma`, at 24 kHz mono.

## Regenerate locally

From this directory, install the local runtime and run the generator:

```sh
npm install kokoro-js
node generate_kokoro.mjs
```

The generator uses the same Kokoro ONNX model and voice for every sample, so the paired tracks isolate the effect of the rewrite prompt/style. The page also links to the primary policy sources used for the scripts.

For an API-backed run, OpenRouter exposes the same model as `hexgrad/kokoro-82m` through its speech endpoint. Keep credentials out of the repository and replace the local fixtures only after checking the resulting files in a browser.
