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
    obiwan: ["obi-wan-kenobi", "ben-obi-wan-kenobi", "ben-kenobi"],
    earlybird: ["early-bird", "early-bird-certificate-package"],
    "early-bird": ["early-bird", "early-bird-certificate-package"],
    coo: ["coo", "country-of-origin", "factory-codes", "vendor-codes"],
    factory: ["factory-codes", "vendor-codes", "coo"],
    vendor: ["vendor-codes", "factory-codes"],
    accessory: ["accessory-production"],
    accessories: ["accessory-production"]
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
    "references",
    "terms",
    "variants",
    "compatibility"
  ];

  const files = [];

  for (const folder of folders) {
    const folderPath = path.join(baseDir, folder);
    const entries = await safeReadDir(folderPath);

    for (const entry of entries) {
      if (!entry.isFile()) continue;

      const ext = path.extname(entry.name).toLowerCase();
      if (ext !== ".txt" && ext !== ".json") continue;

      const stem = entry.name.replace(/\.(txt|json)$/i, "");
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
    if (file.slug === term) score += 40;
    if (file.slug.includes(term)) score += 20;
    if (file.slug.startsWith(term + "-")) score += 15;
  }

  if ((lower.includes("what comes with") || lower.includes("comes with")) && file.folder === "accessories") {
    score += 25;
  }

  if (lower.includes("early bird") && file.slug.includes("early-bird")) {
    score += 60;
  }

  if ((lower.includes("coo") || lower.includes("country of origin")) && file.slug.includes("coo")) {
    score += 60;
  }

  if ((lower.includes("factory") || lower.includes("vendor code")) && (file.slug.includes("factory-codes") || file.slug.includes("vendor-codes"))) {
    score += 60;
  }

  if ((lower.includes("accessory production") || lower.includes("gate scar") || lower.includes("ejector pin")) && file.slug.includes("accessory-production")) {
    score += 60;
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
      entityBase: extractEntityBase(file),
      score: scoreFile(file, message, searchTerms)
    }))
    .filter(f => f.score > 0)
    .sort((a, b) => b.score - a.score)
    .slice(0, 10);

  let context = "";

  for (const file of ranked) {
    const content = await safeReadFile(file.fullPath);
    if (!content.trim()) continue;
    context += `\nFILE: ${file.folder}/${file.name}\n${content}\n`;
  }

  return context;
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

    const context = await buildContext(message);

    const systemPrompt = `
You are VF-CB, a vintage Star Wars figure and accessory expert.

Default assumption:
The user means the original vintage Star Wars toy line from 1977 to 1985 unless they clearly say otherwise.

Important wording rule:
- Do NOT default to saying "Kenner" in every answer
- Prefer "the vintage Star Wars line" or "the original vintage line" unless a specific company or country matters
- Only mention specific brands or companies such as Kenner, Palitoy, PBP, Meccano, Lili Ledy, Glasslite, Toltoys, Top Toys or others when the supplied information supports that detail or the question specifically requires it

Your job:
Answer using the supplied information first.

Your style:
- Speak like an experienced collector
- Be clear, practical, and confident
- Avoid filler or generic explanations

Answer rules:

1. Start with a clear direct answer

2. If variants exist:
   - Briefly mention that deeper variation exists
   - Highlight the most important distinguishing factor

3. If the question is simple:
   - Keep it simple
   - Do not overload the reply

4. If identification, rarity, regional branding, or value is implied:
   - Add relevant collector detail

5. Never invent information

6. Never say a specific mould, factory, accessory type, or version is "the most common" unless that is clearly supported by the supplied information

7. Never mention:
   - files
   - reference files
   - context
   - database
   - prompts
   - or how the answer was generated

Optional personality:
You may add one short polite droid-like opening line occasionally, but do not name or roleplay as C-3PO.

Important behaviour:
- Use real collector logic
- If the answer depends on country, factory, regional branding, or COO, say that clearly
- If the user is likely trying to identify something, guide them naturally toward the next useful question
`;

    const userPrompt = `
Question:
${message}

Supporting information:
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

    if (!response.ok) {
      console.error("Anthropic error:", data);
      return res.status(500).json({
        error: "API error",
        details: data
      });
    }

    return res.status(200).json({
      reply: data?.content?.[0]?.text || "No response"
    });

  } catch (err) {
    console.error(err);
    return res.status(500).json({
      error: "Server error",
      details: err.message
    });
  }
}