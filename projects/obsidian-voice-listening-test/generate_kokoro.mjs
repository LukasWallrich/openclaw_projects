import fs from "node:fs/promises";
import { KokoroTTS } from "kokoro-js";

const project = new URL("./", import.meta.url);
const html = await fs.readFile(new URL("index.html", project), "utf8");
const entityMap = { "&amp;": "&", "&lt;": "<", "&gt;": ">", "&quot;": '"', "&#39;": "'" };
const decode = (value) => value.replace(/&amp;|&lt;|&gt;|&quot;|&#39;/g, (entity) => entityMap[entity]);
const jobs = [...html.matchAll(/<audio[^>]+src="audio\/([^"]+)"[^>]*>[\s\S]*?<p class="transcript">([\s\S]*?)<\/p>/g)]
  .map(([, filename, transcript]) => ({ filename, transcript: decode(transcript.replace(/<[^>]+>/g, "").trim()) }));

if (jobs.length === 0) throw new Error("No audio/transcript pairs found in index.html");

const tts = await KokoroTTS.from_pretrained("onnx-community/Kokoro-82M-v1.0-ONNX", {
  dtype: "q8",
  device: "cpu",
});

for (const { filename, transcript } of jobs) {
  const audio = await tts.generate(transcript, { voice: "bf_emma" });
  await audio.save(new URL(`audio/${filename}`, project));
  console.log(`${filename}\t${transcript.length} characters`);
}
