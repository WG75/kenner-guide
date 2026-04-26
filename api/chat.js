const fs = require("fs");
const path = require("path");

const DATA_ROOT = path.join(process.cwd(), "data");
const MODEL = process.env.ANTHROPIC_MODEL || "claude-haiku-4-5-20251001";

const BLASTER_TERMS = [
  "blaster", "gun", "pistol", "weapon", "accessory", "accessories",
  "laser", "laser gun", "laser pistol", "ray", "ray gun",
  "shooter", "zapper", "pew", "pew pew", "sidearm"
];

const CAPE_CLOAK_TERMS = ["cape", "cloak", "vinyl", "cloth", "robe"];
const FIGURE_TERMS = ["figure", "variant", "coo", "country of origin", "leg mark", "leg marking", "mould", "mold", "paint", "id", "identify", "identification"];

const KNOWN_IMAGE_MAP = [
  {
    match: ["jawa", "blaster"],
    title: "Jawa Blaster Reference",
    url: "https://www.variantvillain.com/wp-content/uploads/2021/12/JawaBlaster_000.jpg",
    caption: "Compare mould shape, rear bump length, plastic colour and detail sharpness."
  },
  {
    match: ["jawa", "vinyl"],
    title: "Jawa Vinyl Cape Authentication Reference",
    url: "/public/images/jawa-vinyl-cape-01.png",
    caption: "Compare cape shape, surface texture on both sides, colour and signs of a cut-down Ben cape."
  }
];

function normalise(text) {
  return String(text || "")
    .toLowerCase()
    .replace(/[^a-z0-9\s\-\/]/g, " ")
    .replace(/\s+/g, " ")
    .trim();
}

function safeReadFile(filePath) {
  try { return fs.readFileSync(filePath, "utf8"); } catch { return ""; }
}

function walkFiles(dir) {
  const results = [];
  if (!fs.existsSync(dir)) return results;
  const items = fs.readdirSync(dir, { withFileTypes: true });
  for (const item of items) {
    const fullPath = path.join(dir, item.name);
    if (item.isDirectory()) results.push(...walkFiles(fullPath));
    else if (/\.(txt|json|md)$/i.test(item.name)) results.push(fullPath);
  }
  return results;
}

function relativeDataPath(filePath) {
  return path.relative(process.cwd(), filePath).replace(/\\/g, "/");
}

function tokenise(text) {
  return normalise(text).split(" ").filter(Boolean).filter((w) => w.length > 1);
}

function detectIntent(message) {
  const t = normalise(message);
  if (BLASTER_TERMS.some((term) => t.includes(term))) return "accessory";
  if (CAPE_CLOAK_TERMS.some((term) => t.includes(term))) return "accessory";
  if (FIGURE_TERMS.some((term) => t.includes(term))) return "figure";
  return "unknown";
}

function scoreFile(filePath, message, intent) {
  const rel = relativeDataPath(filePath).toLowerCase();
  const base = path.basename(filePath).toLowerCase();
  const t = normalise(message);
  const words = tokenise(message);
  let score = 0;

  for (const word of words) {
    if (base.includes(word)) score += 8;
    if (rel.includes(word)) score += 4;
  }

  if (intent === "accessory" && rel.includes("/data/accessories/")) score += 12;
  if (intent === "figure" && rel.includes("/data/figures/")) score += 12;

  if (BLASTER_TERMS.some((term) => t.includes(term))) {
    if (base.includes("blaster")) score += 20;
    if (base.includes("lightsaber")) score += 8;
  }

  if (CAPE_CLOAK_TERMS.some((term) => t.includes(term))) {
    if (base.includes("cape") || base.includes("cloak")) score += 20;
  }

  const entityBoosts = [
    ["jawa", "jawa"], ["luke", "luke"], ["vader", "vader"], ["leia", "leia"],
    ["han", "han"], ["chewbacca", "chewbacca"], ["stormtrooper", "stormtrooper"],
    ["r2", "r2"], ["r2-d2", "r2"], ["c3po", "c-3po"], ["c-3po", "c-3po"]
  ];

  for (const [term, fileTerm] of entityBoosts) {
    if (t.includes(term) && base.includes(fileTerm)) score += 30;
  }

  return score;
}

function selectRelevantFiles(message) {
  const intent = detectIntent(message);
  const allFiles = walkFiles(DATA_ROOT);
  const scored = allFiles
    .map((filePath) => ({ filePath, score: scoreFile(filePath, message, intent) }))
    .filter((item) => item.score > 0)
    .sort((a, b) => b.score - a.score)
    .slice(0, 6);

  const alwaysUseful = [
    path.join(DATA_ROOT, "references", "collector_glossary.txt"),
    path.join(DATA_ROOT, "references", "coo-guide.txt"),
    path.join(DATA_ROOT, "references", "accessory-production.txt"),
    path.join(DATA_ROOT, "terms", "collector_terms.json")
  ].filter((filePath) => fs.existsSync(filePath));

  const merged = [];
  const seen = new Set();
  for (const item of scored) {
    if (!seen.has(item.filePath)) { merged.push(item.filePath); seen.add(item.filePath); }
  }
  for (const filePath of alwaysUseful) {
    if (!seen.has(filePath) && merged.length < 8) { merged.push(filePath); seen.add(filePath); }
  }
  return { intent, files: merged };
}

function buildKnowledgeBlock(files) {
  const maxCharsPerFile = 7000;
  const maxTotalChars = 22000;
  let total = 0;
  const blocks = [];
  for (const filePath of files) {
    const rel = relativeDataPath(filePath);
    let content = safeReadFile(filePath).trim();
    if (!content) continue;
    if (content.length > maxCharsPerFile) content = content.slice(0, maxCharsPerFile) + "\n[TRUNCATED]";
    if (total + content.length > maxTotalChars) break;
    blocks.push(`SOURCE FILE: ${rel}\n${content}`);
    total += content.length;
  }
  return blocks.join("\n\n---\n\n");
}

function getImagesForMessage(message, files) {
  const t = normalise(message);
  const rels = files.map(relativeDataPath).join(" ").toLowerCase();
  const combined = `${t} ${rels}`;
  return KNOWN_IMAGE_MAP.filter((img) => img.match.every((term) => combined.includes(term))).slice(0, 2);
}

function fallbackClarification(files, message) {
  const t = normalise(message);
  if (t.includes("jawa")) {
    return {
      reply: `I’m not sure which Jawa area you mean.\n\nDid you want help with:\n\n1. Jawa figure identification\n2. Jawa blaster / weapon\n3. Jawa cloak or vinyl cape\n\nReply with 1, 2 or 3.`,
      images: [],
      debug: { files: files.map(relativeDataPath), fallback: true }
    };
  }
  return {
    reply: `I’m not sure what you want to identify yet.\n\nTell me the figure or accessory, for example:\n\n• Jawa figure\n• Jawa blaster\n• Luke lightsaber\n• Vader cape`,
    images: [],
    debug: { files: files.map(relativeDataPath), fallback: true }
  };
}

function buildSystemPrompt(knowledgeBlock, selectedFiles, intent) {
  return `You are VF-CB, a Vintage Kenner Star Wars figure and accessory identification assistant.

Rules:
- Use the supplied local reference files as the source of truth.
- Help identify vintage Kenner Star Wars figures, variants, COOs and accessories.
- Ask ONE question at a time.
- Prefer numbered replies.
- Keep answers concise, collector-friendly and practical.
- Do not dump large amounts of information.
- Do not claim something is original unless the evidence is strong.
- For valuable items, warn the user to confirm with experienced collector groups.
- If the user's term is unclear, ask a clarification question rather than guessing.
- If the data file does not support an answer, say so and point them to the relevant reference page if one is in the source.
- For weapons and accessories, mention float tests only when relevant and explain that floating is not proof because modern reproductions may float.
- For grey Jawa blasters, be cautious: grey is commonly repro; rare Glasslite silver exists but should not be assumed.
- For black Jawa blasters, be cautious: it could be repro, modern, very dark blue mistaken for black, or rare Brazilian Glasslite.

Current detected intent: ${intent}

Selected source files:
${selectedFiles.map(relativeDataPath).join("\n")}

Reference data:
${knowledgeBlock}

Return ONLY valid JSON in this shape:
{
  "reply": "message to user",
  "images": []
}

Do not include markdown code fences.`;
}

async function callClaude(systemPrompt, history, message) {
  const apiKey = process.env.ANTHROPIC_API_KEY;
  if (!apiKey) throw new Error("Missing ANTHROPIC_API_KEY");

  const messages = [];
  const cleanHistory = Array.isArray(history) ? history.slice(-12) : [];
  for (const item of cleanHistory) {
    if (!item || !item.role || !item.content) continue;
    if (item.role !== "user" && item.role !== "assistant") continue;
    messages.push({ role: item.role, content: String(item.content).slice(0, 2000) });
  }
  messages.push({ role: "user", content: message });

  const response = await fetch("https://api.anthropic.com/v1/messages", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "x-api-key": apiKey,
      "anthropic-version": "2023-06-01"
    },
    body: JSON.stringify({ model: MODEL, max_tokens: 900, temperature: 0.2, system: systemPrompt, messages })
  });

  const data = await response.json();
  if (!response.ok) throw new Error(data?.error?.message || "Anthropic API error");
  return data?.content?.[0]?.text || "";
}

function parseJsonReply(text) {
  try { return JSON.parse(text); } catch {}
  const start = text.indexOf("{");
  const end = text.lastIndexOf("}");
  if (start !== -1 && end !== -1 && end > start) {
    try { return JSON.parse(text.slice(start, end + 1)); } catch { return null; }
  }
  return null;
}

module.exports = async function handler(req, res) {
  if (req.method !== "POST") {
    res.status(405).json({ error: "Method not allowed" });
    return;
  }

  try {
    const { message, history } = req.body || {};
    const cleanMessage = String(message || "").trim();
    if (!cleanMessage) {
      res.status(400).json({ error: "Missing message" });
      return;
    }

    const { intent, files } = selectRelevantFiles(cleanMessage);
    if (!files.length) {
      res.status(200).json(fallbackClarification([], cleanMessage));
      return;
    }

    const knowledgeBlock = buildKnowledgeBlock(files);
    if (!knowledgeBlock) {
      res.status(200).json(fallbackClarification(files, cleanMessage));
      return;
    }

    const systemPrompt = buildSystemPrompt(knowledgeBlock, files, intent);
    const claudeText = await callClaude(systemPrompt, history, cleanMessage);
    const parsed = parseJsonReply(claudeText);
    const images = getImagesForMessage(cleanMessage, files);

    if (!parsed || !parsed.reply) {
      res.status(200).json({ reply: claudeText || "I found relevant files, but could not format a clean answer.", images, debug: { intent, files: files.map(relativeDataPath) } });
      return;
    }

    res.status(200).json({ reply: parsed.reply, images: Array.isArray(parsed.images) && parsed.images.length ? parsed.images : images, debug: { intent, files: files.map(relativeDataPath) } });
  } catch (err) {
    console.error(err);
    res.status(500).json({ error: err.message || "Server error" });
  }
};
