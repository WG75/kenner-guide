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
    obiwan: ["ben-obi-wan-kenobi", "obi-wan-kenobi", "ben-kenobi"],
    vader: ["darth-vader"],
    tusken: ["sand-people", "tusken-raider"],
    sandpeople: ["sand-people", "tusken-raider"],
    sandcrawler: ["sandcrawler", "jawa"],
    blaster: ["blaster"],
    cloak: ["cloak", "cape"],
    cape: ["cape", "cloak"],
    moc: ["moc", "carded"],
    carded: ["carded", "moc"],
    coo: ["coo", "factory", "factories"],
    factory: ["coo", "factory", "factories"],
    variant: ["variant", "variants"]
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
    "terms",
    "variants",
    "references",
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
        stem,
        slug: slugify(stem),
        fullPath: path.join(folderPath, entry.name)
      });
    }
  }

  return files;
}

function extractEntityBase(file) {
  const slug = file.slug;

  if (file.folder === "figures") {
    if (slug.endsWith("-reference")) {
      return slug.replace(/-reference$/, "");
    }
    return slug;
  }

  const parts = slug.split("-");
  if (parts.length >= 2) {
    return parts[0];
  }

  return slug;
}

function scoreFile(file, message, searchTerms, matchedEntities) {
  const lower = normaliseMessage(message);
  const slug = file.slug;
  const entityBase = extractEntityBase(file);

  let score = 0;

  for (const term of searchTerms) {
    if (slug === term) score += 40;
    if (slug.startsWith(term + "-")) score += 30;
    if (slug.includes(term)) score += 12;
    if (entityBase === term) score += 35;
  }

  for (const entity of matchedEntities) {
    if (entityBase === entity) score += 50;
    if (slug.startsWith(entity + "-")) score += 35;
    if (slug === `${entity}-reference`) score += 70;
    if (slug === entity) score += 60;
  }

  if (lower.includes("what comes with") || lower.includes("comes with")) {
    if (file.folder === "figures") score += 15;
    if (file.folder === "accessories") score += 20;
  }

  if (lower.includes("variant")) {
    if (file.folder === "variants") score += 20;
    if (file.folder === "accessories" || file.folder === "figures") score += 8;
  }

  if (lower.includes("coo") || lower.includes("factory")) {
    if (file.folder === "references" || file.folder === "compatibility") score += 20;
  }

  if (file.folder === "terms") score += 2;

  return score;
}

function detectMatchedEntities(files, searchTerms, message) {
  const lower = normaliseMessage(message);
  const figureBases = unique(
    files
      .filter((f) => f.folder === "figures")
      .map((f) => extractEntityBase(f))
      .filter(Boolean)
  );

  const matched = [];

  for (const base of figureBases) {
    if (searchTerms.includes(base)) {
      matched.push(base);
      continue;
    }

    const spaced = base.replace(/-/g, " ");
    if (lower.includes(spaced)) {
      matched.push(base);
      continue;
    }

    const split = base.split("-");
    if (split.some((part) => searchTerms.includes(part))) {
      matched.push(base);
    }
  }

  return unique(matched);
}

async function buildReferenceContext(message) {
  const baseDir = path.join(process.cwd(), "data");
  const files = await collectFiles(baseDir);
  const searchTerms = getSearchTerms(message);
  const matchedEntities = detectMatchedEntities(files, searchTerms, message);

  const ranked = files
    .map((file) => ({
      ...file,
      entityBase: extractEntityBase(file),
      score: scoreFile(file, message, searchTerms, matchedEntities)
    }))
    .filter((file) => file.score > 0)
    .sort((a, b) => b.score - a.score);

  const selected = [];
  const selectedPaths = new Set();

  for (const entity of matchedEntities) {
    const figurePriority = files.find(
      (f) =>
        f.folder === "figures" &&
        (f.slug === `${entity}-reference` || f.slug === entity)
    );

    if (figurePriority && !selectedPaths.has(figurePriority.fullPath)) {
      selected.push(figurePriority);
      selectedPaths.add(figurePriority.fullPath);
    }

    const related = files
      .filter((f) => extractEntityBase(f) === entity)
      .sort((a, b) => {
        const folderOrder = {
          figures: 1,
          accessories: 2,
          variants: 3,
          references: 4,
          compatibility: 5,
          terms: 6
        };
        return (folderOrder[a.folder] || 99) - (folderOrder[b.folder] || 99);
      });

    for (const file of related) {
      if (!selectedPaths.has(file.fullPath)) {
        selected.push(file);
        selectedPaths.add(file.fullPath);
      }
    }
  }

  for (const file of ranked) {
    if (selected.length >= 10) break;
    if (!selectedPaths.has(file.fullPath)) {
      selected.push(file);
      selectedPaths.add(file.fullPath);
    }
  }

  const glossaryFiles = files.filter(
    (f) =>
      f.folder === "terms" &&
      (f.slug.includes("collector-glossary") || f.slug.includes("collector-terms"))
  );

  for (const file of glossaryFiles) {
    if (selected.length >= 12) break;
    if (!selectedPaths.has(file.fullPath)) {
      selected.push(file);
      selectedPaths.add(file.fullPath);
    }
  }

  const matchedFiles = [];
  const contextBlocks = [];
  let totalChars = 0;
  const maxChars = 22000;

  for (const file of selected) {
    const content = await safeReadFile(file.fullPath);
    if (!content.trim()) continue;

    const block = `FILE: ${file.folder}/${file.name}\n${content.trim()}\n`;
    if (totalChars + block.length > maxChars) break;

    contextBlocks.push(block);
    matchedFiles.push(`${file.folder}/${file.name}`);
    totalChars += block.length;
  }

  return {
    matchedEntities,
    matchedFiles,
    context: contextBlocks.join("\n---\n\n")
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
    const { matchedEntities, matchedFiles, context } = await buildReferenceContext(message);

    const systemPrompt = `
You are VF-CB, a Vintage Star Wars Kenner expert.

Default assumption:
The user means the original Kenner toy line from 1977 to 1985 unless they clearly ask about something else.

Your job:
Answer using the supplied local reference files first.
Do not fall back to generic Star Wars lore if the local files contain the answer.
Do not invent accessories, variants, dates, factories, COO details, or packaging information.

Rules:
- Prioritise local reference context over your own memory
- Be concise, specific, and collector-friendly
- Use British English
- If local files are incomplete, say so briefly instead of pretending certainty
- For "what comes with" questions, state the standard accessory first, then important variant differences
- Keep the answer focused on vintage Kenner unless the user clearly asks otherwise

Important Jawa rules:
- Standard accessory: Jawa Blaster
- Early rare release: vinyl cape
- Later more common release: cloth cloak
- Do not describe the vinyl cape as the standard accessory
- The Jawa's eyes should be described as yellow, not glowing

When useful, end with one short follow-up question about identifying a specific loose figure, MOC, COO, factory item, or variant.
`;

    const userPrompt = `
User question:
${message}

Matched entity bases:
${matchedEntities.length ? matchedEntities.join(", ") : "None"}

Matched files:
${matchedFiles.length ? matchedFiles.join(", ") : "None"}

Local reference context:
${context || "No local reference context matched."}

Answer the question using the local reference context first.
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
      matchedEntities,
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
