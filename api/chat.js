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

function getSearchTerms(message) {
  const lower = normaliseMessage(message);

  const rawWords = lower.match(/[a-z0-9'-]+/g) || [];
  const words = rawWords.map(slugify).filter(Boolean);

  const aliases = {
    jawa: ["jawa"],
    jawas: ["jawa"],
    luke: ["luke-skywalker"],
    leia: ["princess-leia-organa"],
    chewy: ["chewbacca"],
    vader: ["darth-vader"],
    obiwan: ["obi-wan-kenobi"],
    earlybird: ["early-bird", "early-bird-certificate-package"]
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
  const folders = ["figures", "accessories", "references"];
  const files = [];

  for (const folder of folders) {
    const folderPath = path.join(baseDir, folder);
    const entries = await safeReadDir(folderPath);

    for (const entry of entries) {
      if (!entry.isFile()) continue;

      if (!entry.name.endsWith(".txt")) continue;

      files.push({
        folder,
        name: entry.name,
        slug: slugify(entry.name.replace(".txt", "")),
        fullPath: path.join(folderPath, entry.name)
      });
    }
  }

  return files;
}

function scoreFile(file, message, searchTerms) {
  let score = 0;
  const lower = normaliseMessage(message);

  for (const term of searchTerms) {
    if (file.slug.includes(term)) score += 20;
  }

  if (file.folder === "figures") score += 5;

  // Smart boosts for reference knowledge
  if (lower.includes("what comes with") || lower.includes("identify")) {
    if (file.folder === "references") score += 10;
  }

  if (lower.includes("variant") || lower.includes("difference")) {
    if (file.folder === "references") score += 20;
  }

  if (lower.includes("early bird")) {
    if (file.slug.includes("early-bird")) score += 50;
  }

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
    .slice(0, 10);

  let context = "";

  for (const file of ranked) {
    const content = await safeReadFile(file.fullPath);
    if (content.trim()) {
      context += `\n${content}\n`;
    }
  }

  return context;
}

export default async function handler(req, res) {
  try {
    const { message } = req.body;

    const context = await buildContext(message);

    const systemPrompt = `
You are VF-CB, a vintage Star Wars figure and accessory expert.

Default assumption:
The user means the original vintage Star Wars toy line from 1977 to 1985 unless they clearly say otherwise.

Important wording rule:
- Do NOT default to saying "Kenner"
- Only mention specific companies (Kenner, Palitoy, Meccano, PBP, Lili Ledy, etc.) when relevant

Your job:
Answer using the supplied information first.

Answer style:
- Speak like an experienced collector
- Be clear, practical, and direct
- Avoid filler

Core behaviour:

1. Start with a direct answer

2. If the topic involves accessories or identification:
   - Briefly guide the user on how collectors identify it
   - Reference key factors like:
     • body covering
     • COO
     • mould type
     • production differences

3. If variants exist:
   - Mention them naturally
   - Highlight what actually matters

4. Never invent information

5. Never claim something is "most common" unless clearly supported

6. Never mention:
   - files
   - context
   - system
   - database

Optional personality:
You may add one short polite droid-like opening line occasionally.
Do not roleplay as a named character.

Goal:
Sound like a knowledgeable collector helping another collector identify or understand something.
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