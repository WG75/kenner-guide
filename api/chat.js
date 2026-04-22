import fs from "fs/promises";
import path from "path";

function slugify(text) {
  return String(text || "")
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "");
}

function unique(array) {
  return [...new Set(array)];
}

function getKeywords(message) {
  const cleaned = String(message || "").toLowerCase();

  const synonymMap = {
    jawa: ["jawa"],
    jawas: ["jawa"],
    chewie: ["chewbacca"],
    chewy: ["chewbacca"],
    obiwan: ["ben-obi-wan-kenobi", "ben-kenobi", "obi-wan-kenobi"],
    leia: ["princess-leia-organa", "leia"],
    luke: ["luke-skywalker", "farmboy-luke", "luke"],
    vader: ["darth-vader", "vader"],
    tusken: ["sand-people", "tusken-raider"],
    sandpeople: ["sand-people", "tusken-raider"],
    blaster: ["blaster"],
    cape: ["cape", "cloak"],
    cloak: ["cloak", "cape"],
    lightsaber: ["lightsaber", "telescoping-lightsaber", "double-telescoping-lightsaber"],
    coo: ["coo", "factory", "factories"],
    factory: ["factory", "factories", "coo"],
    variant: ["variant", "variants"],
    moc: ["moc", "carded"],
    carded: ["carded", "moc"],
  };

  const rawWords = cleaned.match(/[a-z0-9'-]+/g) || [];
  const filtered = rawWords.filter((w) => w.length > 2);

  let expanded = [...filtered];

  for (const word of filtered) {
    if (synonymMap[word]) expanded.push(...synonymMap[word]);
  }

  return unique(expanded.map(slugify)).filter(Boolean);
}

async function fileExists(filePath) {
  try {
    await fs.access(filePath);
    return true;
  } catch {
    return false;
  }
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

async function collectCandidateFiles(baseDir) {
  const subfolders = [
    "figures",
    "accessories",
    "terms",
    "variants",
    "references",
    "compatibility",
  ];

  const files = [];

  for (const folder of subfolders) {
    const folderPath = path.join(baseDir, folder);
    const entries = await safeReadDir(folderPath);

    for (const entry of entries) {
      if (!entry.isFile()) continue;

      const ext = path.extname(entry.name).toLowerCase();
      if (ext !== ".txt" && ext !== ".json") continue;

      files.push({
        folder,
        name: entry.name,
        fullPath: path.join(folderPath, entry.name),
        slug: slugify(entry.name.replace(/\.(txt|json)$/i, "")),
      });
    }
  }

  const rootFiles = await safeReadDir(baseDir);
  for (const entry of rootFiles) {
    if (!entry.isFile()) continue;

    const ext = path.extname(entry.name).toLowerCase();
    if (ext !== ".txt" && ext !== ".json") continue;

    files.push({
      folder: "root",
      name: entry.name,
      fullPath: path.join(baseDir, entry.name),
      slug: slugify(entry.name.replace(/\.(txt|json)$/i, "")),
    });
  }

  return files;
}

function scoreFile(file, keywords, fullMessage) {
  let score = 0;
  const lowerMessage = fullMessage.toLowerCase();

  for (const keyword of keywords) {
    if (file.slug === keyword) score += 30;
    if (file.slug.includes(keyword)) score += 12;
    if (keyword.includes(file.slug)) score += 8;
  }

  if (file.folder === "figures") score += 2;
  if (file.folder === "accessories") score += 1;

  if (lowerMessage.includes("what comes with") || lowerMessage.includes("comes with")) {
    if (file.folder === "figures") score += 5;
    if (file.folder === "accessories") score += 5;
  }

  if (lowerMessage.includes("variant")) {
    if (file.folder === "variants") score += 6;
  }

  if (lowerMessage.includes("coo") || lowerMessage.includes("factory")) {
    if (file.folder === "references" || file.folder === "root") score += 4;
  }

  return score;
}

async function buildReferenceContext(message) {
  const baseDir = path.join(process.cwd(), "data");
  const hasData = await fileExists(baseDir);

  if (!hasData) {
    return {
      context: "",
      matchedFiles: [],
      note: "No local data folder found.",
    };
  }

  const keywords = getKeywords(message);
  const allFiles = await collectCandidateFiles(baseDir);

  const ranked = allFiles
    .map((file) => ({
      ...file,
      score: scoreFile(file, keywords, message),
    }))
    .filter((file) => file.score > 0)
    .sort((a, b) => b.score - a.score);

  const alwaysInclude = allFiles.filter(
    (f) =>
      f.folder === "terms" ||
      f.slug === "factories" ||
      f.slug === "collector-terms" ||
      f.slug === "collector-glossary"
  );

  const selected = unique(
    [...ranked.slice(0, 8), ...alwaysInclude.slice(0, 3)].map((f) => f.fullPath)
  )
    .slice(0, 10);

  const matchedFiles = [];
  const parts = [];
  let totalChars = 0;
  const maxChars = 18000;

  for (const filePath of selected) {
    const file = allFiles.find((f) => f.fullPath === filePath);
    if (!file) continue;

    const content = await safeReadFile(file.fullPath);
    if (!content.trim()) continue;

    const block = `FILE: ${file.folder}/${file.name}\n${content.trim()}\n`;
    if (totalChars + block.length > maxChars) break;

    parts.push(block);
    matchedFiles.push(`${file.folder}/${file.name}`);
    totalChars += block.length;
  }

  return {
    context: parts.join("\n---\n\n"),
    matchedFiles,
    note: matchedFiles.length ? "" : "No strongly matching local files found.",
  };
}

export default async function handler(req, res) {
  try {
    if (req.method !== "POST") {
      return res.status(405).json({ error: "Method not allowed" });
    }

    const { message } = req.body || {};

    if (!message) {
      return res.status(400).json({ error: "No message provided" });
    }

    const MODEL = "claude-haiku-4-5";
    const { context, matchedFiles, note } = await buildReferenceContext(message);

    const systemPrompt = `
You are VF-CB, a Vintage Star Wars Kenner expert.

Default assumption:
The user is asking about the original Kenner toy line from 1977 to 1985 unless they clearly say otherwise.

Your job:
Answer using the supplied local reference files first.
Do not rely on generic Star Wars lore when the reference files provide the answer.
Do not invent accessories, variants, dates, packaging details, COO details, or vehicle contents.

Rules:
- Prioritise the local reference context over your own memory
- If the local context is silent or incomplete, say so briefly instead of guessing
- Use concise, collector-friendly language
- Use British English
- For "what comes with" questions, state the standard accessory first, then important variant differences
- Keep answers focused on vintage Kenner unless the user clearly asks about something else

Important Jawa rules:
- Standard accessory: Jawa Blaster
- Early rare releases: vinyl cape
- Later, more common releases: cloth cloak
- Do not describe the vinyl cape as the standard accessory
- Describe the eyes as yellow, not glowing

When useful, end with one short follow-up question about identifying a specific loose figure, MOC, COO, or variant.
`;

    const userPrompt = `
User question:
${message}

Local reference context:
${context || "No local reference context was matched."}

Matched files:
${matchedFiles.length ? matchedFiles.join(", ") : "None"}

Additional note:
${note || "None"}

Answer the user using the local reference context first.
`;

    const response = await fetch("https://api.anthropic.com/v1/messages", {
      method: "POST",
      headers: {
        "content-type": "application/json",
        "x-api-key": process.env.ANTHROPIC_API_KEY,
        "anthropic-version": "2023-06-01"
      },
      body: JSON.stringify({
        model: MODEL,
        max_tokens: 700,
        system: systemPrompt,
        messages: [
          {
            role: "user",
            content: userPrompt
          }
        ]
      })
    });

    const data = await response.json();

    if (!response.ok) {
      console.error("Anthropic error:", data);
      return res.status(500).json({
        error: "API error",
        details: data
      });
    }

    return res.status(200).json({
      reply: data?.content?.[0]?.text || "No response from AI",
      matchedFiles
    });

  } catch (err) {
    console.error("Server error:", err);
    return res.status(500).json({
      error: "Server error",
      details: err.message
    });
  }
}
