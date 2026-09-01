# Obsidian voice listening test

This fixture contains five short AI-policy notes, each with two rewrite styles, plus a pronunciation lab that reads one fixed stress-test script in four voices. It is for comparing spoken-summary scripts and synthesis quality before wiring the pipeline into the Obsidian bridge.

The checked-in note audio is deliberately short excerpts (about 25–28 seconds each), not the target 3–5 minute production summaries. The pronunciation tracks use the same text in `bf_emma`, `bm_george`, `af_heart`, and `am_michael`. All local fixtures were generated with Kokoro-82M at 24 kHz mono.

## Regenerate locally

From this directory, install the local runtime and run the generator:

```sh
npm install kokoro-js
node generate_kokoro.mjs
```

The generator uses the same Kokoro ONNX model for every sample. The paired note tracks isolate rewrite style, while the pronunciation tracks isolate voice choice. The page also links to the primary policy sources used for the scripts.

For an API-backed run, OpenRouter exposes the same model as `hexgrad/kokoro-82m` through its speech endpoint. Keep credentials out of the repository and replace the local fixtures only after checking the resulting files in a browser.
