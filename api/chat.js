import fs from "fs/promises";
import path from "path";

function slugify(text) {
  return String(text || "")
    .toLowerCase()
    .replace(/\.txt$/i, "")
    .replace(/\.json$/i, "")
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "");
}

function unique(arr) {
  return [...new Set(arr)];
}

function normaliseMessage(text) {
  return String(text || "").toLowerCase();
}

function getSearchTerms(message) {
  const lower = normaliseMessage(message);

  const rawWords = lower.match(/[a-z0-9'-]+/g) || [];
  const words = rawWords.map(slugify).filter(Boolean);

  const aliases = {
    jawa: ["jawa"],
    jawas: ["jawa"],
    luke: ["luke-skywalker"],
    leia: ["princess-leia-organa", "leia"],
    chewy: ["chewbacca"],
    chewie: ["chewbacca"],
    vader: ["darth-vader"],
    obiwan: ["obi-wan-kenobi"],
    earlybird: ["early-bird", "early-bird-certificate-package"],
    "early-bird": ["early-bird", "early-bird-certificate-package"]
  };

  const expanded = [...words];

  for (const word of words) {
    if (aliases[word]) {
      expanded.push(...aliases[word]);
    }
  }

  return unique(expanded.map(slugify)).filter(Boolean);
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
  const folders = [
    "figures",
    "accessories",
    "references"
  ];

  const files = [];

  for (const folder of folders) {
    const folderPath = path.join(baseDir, folder);
    const entries = await safeReadDir(folderPath);

    for (const entry of entries) {
      if (!entry.isFile()) continue;

      const ext = path.extname(entry.name).toLowerCase();
      if (ext !== ".txt") continue;

      const stem = entry.name.replace(/\.txt$/i, "");
      files.push({
        folder,
        name: entry.name,
        slug: slugify(stem),
        fullPath: path.join(folderPath, entry.name)
      });
    }
  }

  return files;
}

function extractEntityBase(file) {
  if (file.folder === "figures") {
    return file.slug.replace("-reference", "");
  }
  return file.slug.split("-")[0];
}

function scoreFile(file, message, searchTerms) {
  const lower = normaliseMessage(message);
  let score = 0;

  for (const term of searchTerms) {
    if (file.slug.includes(term)) score += 20;
  }

  if (lower.includes("what comes with") && file.folder === "accessories") {
    score += 25;
  }

  if (lower.includes("early bird") && file.slug.includes("early-bird")) {
    score += 50;
  }

  if (file.folder === "figures") score += 5;

  return score;
}

async function buildContext(message) {
  const baseDir = path.join(process.cwd(), "data");
  const files = await collectFiles(baseDir);
  const searchTerms = getSearchTerms(message);

  const ranked = files
    .map(file => ({
      ...file,
      score: scoreFile(file, message, searchTerms)
    }))
    .filter(f => f.score > 0)
    .sort((a, b) => b.score - a.score)
    .slice(0, 8);

  let context = "";

  for (const file of ranked) {
    const content = await safeReadFile(file.fullPath);
    context += `\n${content}\n`;
  }

  return context;
}

export default async function handler(req, res) {
  try {
    if (req.method !== "POST") {
      return res.status(405).json({ error: "Method not allowed" });
    }

    const { message } = req.body;

    if (!message) {
      return res.status(400).json({ error: "No message provided" });
    }

    const context = await buildContext(message);

    const systemPrompt = `
You are VF-CB, a Vintage Star Wars Kenner expert.

Default assumption:
The user means the original Kenner toy line from 1977 to 1985 unless they clearly say otherwise.

Your job:
Answer using the supplied information first.

Your style:
- Speak like an experienced collector
- Be clear, practical, and confident
- Avoid filler or generic explanations

Answer rules:

1. Start with a clear direct answer

2. If variants exist:
   - Briefly mention them
   - Highlight the most important difference

3. If the question is simple:
   - Keep it simple

4. If identification or value is implied:
   - Add relevant collector detail

5. Never invent information

6. Never mention:
   - files
   - context
   - database
   - system

Optional personality:
You may add ONE short polite C-3PO-style opening line occasionally.
Keep it brief and do not let it affect clarity.

Important:
- Use real collector logic
- Guide the user naturally if they are identifying something
`;

    const userPrompt = `
Question:
${message}

Information:
${context}
`;

    const response = await fetch("https://api.anthropic.com/v1/messages", {
      method: "POST",
      headers: {
        "content-type": "application/json",
        "x-api-key": process.env.ANTHROPIC_API_KEY,
        "anthropic-version": "2023-06-01"
      },
      body: JSON.stringify({
        model: "claude-haiku-4-5",
        max_tokens: 700,
        system: systemPrompt,
        messages: [{ role: "user", content: userPrompt }]
      })
    });

    const data = await response.json();

    return res.status(200).json({
      reply: data?.content?.[0]?.text || "No response"
    });

  } catch (err) {
    console.error(err);
    return res.status(500).json({
      error: "Server error"
    });
  }
}