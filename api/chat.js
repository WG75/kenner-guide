import fs from "fs/promises";
import path from "path";

function slugify(text) {
  return String(text || "")
    .toLowerCase()
    .replace(/\.txt$/i, "")
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "");
}

function unique(arr) {
  return [...new Set(arr)];
}

function normaliseMessage(text) {
  return String(text || "").toLowerCase();
}

function sanitiseHistory(history) {
  if (!Array.isArray(history)) return [];
  return history
    .filter(
      m =>
        m &&
        typeof m.content === "string" &&
        (m.role === "user" || m.role === "assistant")
    )
    .slice(-12);
}

function detectActiveFigure(message, history = []) {
  const combined = [
    ...history.map(m => m?.content || ""),
    message || ""
  ].join(" ");

  const lower = normaliseMessage(combined);

  if (lower.includes("jawa")) return "jawa";
  if (lower.includes("luke")) return "luke-skywalker";
  if (lower.includes("leia")) return "princess-leia-organa";
  if (lower.includes("chewbacca")) return "chewbacca";
  if (lower.includes("r2")) return "r2-d2";

  return "";
}

function expandShortReply(message, activeFigure) {
  const m = message.trim().toLowerCase();

  if (!activeFigure) return message;

  if (m === "cloth")
    return `User is identifying a ${activeFigure} and confirms it has a cloth cape (fabric hooded garment).`;

  if (m === "vinyl")
    return `User is identifying a ${activeFigure} and confirms it has a vinyl cape (thin brown plastic).`;

  if (m === "no cape" || m === "naked")
    return `User is identifying a ${activeFigure} and confirms the figure has no cape or cloak present.`;

  return message;
}

async function safeReadDir(dirPath) {
  try {
    return await fs.readdir(dirPath, { withFileTypes: true });
  } catch {
    return [];
  }
}

async function safeReadFile(filePath) {
  try {
    return await fs.readFile(filePath, "utf8");
  } catch {
    return "";
  }
}

async function collectFiles(baseDir) {
  const folders = ["figures", "accessories", "references"];
  const files = [];

  for (const folder of folders) {
    const folderPath = path.join(baseDir, folder);
    const entries = await safeReadDir(folderPath);

    for (const entry of entries) {
      if (entry.isFile() && entry.name.endsWith(".txt")) {
        files.push({
          folder,
          name: entry.name,
          slug: slugify(entry.name),
          fullPath: path.join(folderPath, entry.name)
        });
      }
    }
  }

  return files;
}

async function buildContext(message, history, activeFigure) {
  const baseDir = path.join(process.cwd(), "data");
  const files = await collectFiles(baseDir);

  let context = "";

  for (const file of files) {
    if (activeFigure && !file.slug.includes(activeFigure)) continue;

    const content = await safeReadFile(file.fullPath);
    if (content) context += `\n${content}\n`;
  }

  return context.slice(0, 12000);
}

export default async function handler(req, res) {
  try {
    const { message, history = [] } = req.body;

    const cleanHistory = sanitiseHistory(history);
    const activeFigure = detectActiveFigure(message, cleanHistory);
    const expanded = expandShortReply(message, activeFigure);
    const context = await buildContext(expanded, cleanHistory, activeFigure);

    const systemPrompt = `
You are VF-CB, a vintage Star Wars figure expert.

Rules:
- Stay locked on the current figure (do NOT switch figures)
- "No cape" means the figure is missing it, NOT a different character
- Collectors often call both vinyl and cloth versions simply "cape"
- NEVER assume rarity or say "most common" unless confirmed
- Guide step-by-step identification logically
- Do NOT restart or reintroduce yourself
`;

    const response = await fetch("https://api.openai.com/v1/responses", {
      method: "POST",
      headers: {
        "Authorization": `Bearer ${process.env.OPENAI_API_KEY}`,
        "Content-Type": "application/json"
      },
      body: JSON.stringify({
        model: "gpt-5.4",
        input: [
          {
            role: "system",
            content: systemPrompt
          },
          {
            role: "user",
            content: `
User message:
${message}

Expanded:
${expanded}

Active figure:
${activeFigure}

Context:
${context}
`
          }
        ],
        max_output_tokens: 600
      })
    });

    const data = await response.json();

    return res.status(200).json({
      reply: data.output?.[0]?.content?.[0]?.text || "No response"
    });

  } catch (err) {
    return res.status(500).json({ error: err.message });
  }
}
