import fs from "node:fs/promises";
import { KokoroTTS } from "kokoro-js";

const project = new URL("./", import.meta.url);
const html = await fs.readFile(new URL("index.html", project), "utf8");
const entityMap = { "&amp;": "&", "&lt;": "<", "&gt;": ">", "&quot;": '"', "&#39;": "'" };
const decode = (value) => value.replace(/&amp;|&lt;|&gt;|&quot;|&#39;/g, (entity) => entityMap[entity]);
const jobs = [...html.matchAll(/<audio[^>]+src="audio\/([^"]+)"[^>]*>[\s\S]*?<p class="transcript">([\s\S]*?)<\/p>/g)]
  .map(([, filename, transcript]) => ({ filename, voice: "bf_emma", transcript: decode(transcript.replace(/<[^>]+>/g, "").trim()) }));

const pronunciationText = "Article 50 of the European Union AI Act covers GPAI, or general-purpose artificial intelligence. The European Commission published its guidance in 2026. NIST and HEPI are separate organisations. A 24.5 percent change is not the same as 2.45 percent. The proposal is voluntary, not mandatory; and a legislative recommendation is not a law. Check the URL, example dot org slash AI dash policy.";
for (const [voice, filename] of [["bf_emma", "pronunciation-bf-emma.wav"], ["bm_george", "pronunciation-bm-george.wav"], ["af_heart", "pronunciation-af-heart.wav"], ["am_michael", "pronunciation-am-michael.wav"]]) {
  jobs.push({ filename, voice, transcript: pronunciationText });
}

if (jobs.length === 0) throw new Error("No audio/transcript pairs found in index.html");

const tts = await KokoroTTS.from_pretrained("onnx-community/Kokoro-82M-v1.0-ONNX", {
  dtype: "q8",
  device: "cpu",
});

for (const { filename, transcript } of jobs) {
  const voice = jobs.find((job) => job.filename === filename).voice;
  const audio = await tts.generate(transcript, { voice });
  await audio.save(new URL(`audio/${filename}`, project));
  console.log(`${filename}\t${voice}\t${transcript.length} characters`);
}
