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

function getSearchTerms(message, history = [], activeFigure = "") {
  const combined = [
    ...history.map(m => m?.content || ""),
    message || "",
    activeFigure || ""
  ].join(" ");

  const lower = normaliseMessage(combined);
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
    ben: ["obi-wan-kenobi", "ben-obi-wan-kenobi", "ben-kenobi"],
    earlybird: ["early-bird", "early-bird-certificate-package"],
    "early-bird": ["early-bird", "early-bird-certificate-package"]
  };

  const expanded = [...words];

  for (const word of words) {
    if (aliases[word]) {
      expanded.push(...aliases[word]);
    }
  }

  if (activeFigure) {
    expanded.push(activeFigure);
  }

  return unique(expanded.map(slugify)).filter(Boolean);
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

function buildTranscript(history) {
  if (!history.length) return "None";

  return history
    .map(m => `${m.role === "user" ? "User" : "VF-CB"}: ${m.content}`)
    .join("\n\n");
}

function isShortFollowUp(message) {
  const trimmed = String(message || "").trim().toLowerCase();
  if (!trimmed) return false;
  return trimmed.split(/\s+/).length <= 5;
}

function detectActiveFigure(message, history = []) {
  const combined = [
    ...history.map(m => m?.content || ""),
    message || ""
  ].join(" ");

  const lower = normaliseMessage(combined);

  const figurePatterns = [
    { key: "jawa", patterns: ["jawa", "jawas"] },
    { key: "luke-skywalker", patterns: ["luke skywalker", "luke"] },
    { key: "princess-leia-organa", patterns: ["princess leia", "leia"] },
    { key: "chewbacca", patterns: ["chewbacca", "chewie", "chewy"] },
    { key: "r2-d2", patterns: ["r2-d2", "r2d2", "r2"] },
    { key: "darth-vader", patterns: ["darth vader", "vader"] },
    { key: "obi-wan-kenobi", patterns: ["obi-wan", "obi wan", "ben kenobi", "ben"] },
    { key: "sand-people", patterns: ["sand people", "tusken", "tusken raider"] }
  ];

  let found = "";

  for (const figure of figurePatterns) {
    for (const pattern of figure.patterns) {
      if (lower.includes(pattern)) {
        found = figure.key;
      }
    }
  }

  return found;
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

function scoreFile(file, message, searchTerms, history = [], activeFigure = "") {
  let score = 0;
  const combined = `${history.map(h => h.content || "").join(" ")} ${message}`;
  const lower = normaliseMessage(combined);

  for (const term of searchTerms) {
    if (file.slug.includes(term)) score += 20;
  }

  if (file.folder === "figures") score += 5;

  if (lower.includes("identify") || lower.includes("which") || lower.includes("difference")) {
    if (file.folder === "references") score += 15;
  }

  if (lower.includes("what comes with")) {
    if (file.folder === "accessories") score += 25;
  }

  if (lower.includes("early bird") && file.slug.includes("early-bird")) {
    score += 50;
  }

  if (activeFigure) {
    if (file.slug.includes(activeFigure)) score += 60;
    if (file.folder === "figures" && file.slug === `${activeFigure}-reference`) score += 80;
  }

  return score;
}

async function buildContext(message, history = [], activeFigure = "") {
  const baseDir = path.join(process.cwd(), "data");
  const files = await collectFiles(baseDir);
  const searchTerms = getSearchTerms(message, history, activeFigure);

  const ranked = files
    .map(file => ({
      ...file,
      score: scoreFile(file, message, searchTerms, history, activeFigure)
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
    if (req.method !== "POST") {
      return res.status(405).json({ error: "Method not allowed" });
    }

    const { message, history = [] } = req.body || {};

    if (!message || typeof message !== "string") {
      return res.status(400).json({ error: "No message provided" });
    }

    const cleanHistory = sanitiseHistory(history);
    const activeFigure = detectActiveFigure(message, cleanHistory);
    const context = await buildContext(message, cleanHistory, activeFigure);
    const transcript = buildTranscript(cleanHistory);
    const shortFollowUp = isShortFollowUp(message);

    const systemPrompt = `
You are VF-CB, a vintage Star Wars figure and accessory expert.

Default assumption:
The user means the original vintage Star Wars toy line from 1977 to 1985.

Important wording rules:
- Do NOT default to "Kenner"
- Only mention specific companies when relevant

Critical accuracy rules:

1. ONLY state specific claims such as "most common", "rarer", "typical", "usually found", or similar if they are clearly supported by the supplied information

2. If the supplied information does not confirm something:
   - Do NOT guess
   - Do NOT generalise
   - Do NOT add assumptions

3. Avoid stating obvious physical traits unless they add real identification value

Answer style:
- Speak like an experienced collector
- Be clear, direct, and practical
- Prioritise useful identification insight over general description

Collector logic:

1. Always prioritise the most useful identifier first

Examples:
- Jawa identification → first ask whether it has a vinyl cape, cloth cloak, or no body covering present
- If cloth cloak Jawa → hood shape before stitching detail
- Luke → DT vs ST first

2. For incomplete loose figures, still help identify them using figure traits even if accessories are missing

3. After the first obvious identifier, guide the user toward the next useful checks:
- COO / leg markings
- mould traits
- paint colour
- plastic colour
- figure assembly traits

4. Make it clear that COO alone is not enough to confirm a figure's origins

5. If the latest user message is short, such as:
- cloth
- vinyl
- no blaster
- hong kong
- taiwan
- no coo
then treat it as a direct reply to the previous identification question and continue the same conversation

6. If an active figure has already been established in the recent conversation, stay locked on that figure unless the user clearly changes subject

7. Do not switch to another figure just because a word such as "cape", "vinyl", "cloth", or "hood" could also apply elsewhere

8. Do not restart the conversation or reintroduce yourself unless the user clearly starts a new topic

Never:
- Invent information
- Assume rarity or frequency
- State "most common" without explicit support
- Mention files, context, or system

Optional personality:
You may add one short polite droid-like opening line occasionally.
Do not roleplay as a named character.

Goal:
Sound like a knowledgeable collector helping another collector identify or understand something, using only grounded, reliable information.
`;

    const userPrompt = `
Current user message:
${message}

Short follow-up reply?
${shortFollowUp ? "Yes" : "No"}

Active figure/topic from the recent conversation:
${activeFigure || "None clearly established"}

Recent conversation:
${transcript}

Supporting information:
${context}

Instructions for this turn:
- Use the recent conversation to understand what the user means
- If the current message is a short follow-up, continue from the previous question
- If an active figure/topic is already established, stay on that figure/topic
- Do not restart or introduce yourself again
- Move the identification forward by asking or answering the next useful step
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
