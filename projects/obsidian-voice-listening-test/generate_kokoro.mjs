import fs from "node:fs/promises";
import { execFileSync } from "node:child_process";
import { fileURLToPath } from "node:url";
import { KokoroTTS } from "kokoro-js";

const project = new URL("./", import.meta.url);
const html = await fs.readFile(new URL("index.html", project), "utf8");
const entityMap = { "&amp;": "&", "&lt;": "<", "&gt;": ">", "&quot;": '"', "&#39;": "'" };
const decode = (value) => value.replace(/&amp;|&lt;|&gt;|&quot;|&#39;/g, (entity) => entityMap[entity]);
const jobs = [...html.matchAll(/<audio[^>]+src="audio\/([^"]+)"[^>]*>[\s\S]*?<p class="transcript">([\s\S]*?)<\/p>/g)]
  .map(([, filename, transcript]) => ({ filename, voice: "bf_emma", transcript: decode(transcript.replace(/<[^>]+>/g, "").trim()) }));

const pronunciationText = "Article 50 of the European Union AI Act covers GPAI, or general-purpose artificial intelligence. The European Commission published its guidance in 2026. NIST and HEPI are separate organisations. A 24.5 percent change is not the same as 2.45 percent. The proposal is voluntary, not mandatory; and a legislative recommendation is not a law. Check the URL, example dot org slash AI dash policy.";
for (const [voice, filename] of [["bf_emma", "pronunciation-bf-emma.mp3"], ["bm_george", "pronunciation-bm-george.mp3"], ["af_heart", "pronunciation-af-heart.mp3"], ["am_michael", "pronunciation-am-michael.mp3"]]) {
  jobs.push({ filename, voice, transcript: pronunciationText });
}

const acronymVariants = [
  ["acronyms-spaces-bf-emma.mp3", "G P A I. N I S T. H E P I. U R L. Article 50. Twenty-four point five percent. Voluntary, not mandatory."],
  ["acronyms-dots-bf-emma.mp3", "G. P. A. I. N. I. S. T. H. E. P. I. U. R. L. Article 50. Twenty-four point five percent. Voluntary, not mandatory."],
  ["acronyms-spoken-bf-emma.mp3", "Gee pee ay eye. En eye ess tee. Aitch ee pee eye. You are ell. Article fifty. Twenty-four point five percent. Voluntary, not mandatory."],
  ["acronyms-expanded-bf-emma.mp3", "General-purpose artificial intelligence, abbreviated G P A I. The National Institute of Standards and Technology, or N I S T. The Higher Education Policy Institute, or H E P I. The uniform resource locator, or U R L. Article 50. Twenty-four point five percent. Voluntary, not mandatory."],
];
for (const [filename, transcript] of acronymVariants) jobs.push({ filename, voice: "bf_emma", transcript });

if (jobs.length === 0) throw new Error("No audio/transcript pairs found in index.html");

const tts = await KokoroTTS.from_pretrained("onnx-community/Kokoro-82M-v1.0-ONNX", {
  dtype: "q8",
  device: "cpu",
});

// Kokoro writes WAV; the page serves 64 kbps mono MP3, so convert on the way out.
for (const { filename, voice, transcript } of jobs) {
  const audio = await tts.generate(transcript, { voice });
  const scratch = new URL(`audio/${filename.replace(/\.mp3$/, "")}.scratch.wav`, project);
  await audio.save(scratch);
  execFileSync("ffmpeg", ["-v", "error", "-y", "-i", fileURLToPath(scratch),
    "-ac", "1", "-ar", "24000", "-b:a", "64k",
    fileURLToPath(new URL(`audio/${filename}`, project))]);
  await fs.rm(scratch);
  console.log(`${filename}\t${voice}\t${transcript.length} characters`);
}
