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
  if (lower.includes("vader")) return "darth-vader";
  if (lower.includes("obi-wan") || lower.includes("obi wan") || lower.includes("ben kenobi")) return "obi-wan-kenobi";

  return "";
}

function expandShortReply(message, activeFigure) {
  const m = String(message || "").trim().toLowerCase();

  if (!activeFigure) return message;

  if (m === "cloth") {
    return `User is identifying a ${activeFigure} and confirms it has a cloth cape or cloak.`;
  }

  if (m === "vinyl") {
    return `User is identifying a ${activeFigure} and confirms it has a vinyl cape.`;
  }

  if (m === "no cape" || m === "naked") {
    return `User is identifying a ${activeFigure} and confirms the figure has no cape or cloak present.`;
  }

  if (m === "no blaster") {
    return `User is identifying a ${activeFigure} and confirms the weapon accessory is missing.`;
  }

  if (m === "hong kong" || m === "taiwan" || m === "china" || m === "macau") {
    return `User is identifying a ${activeFigure} and confirms the COO marking is ${m}.`;
  }

  if (m === "no coo") {
    return `User is identifying a ${activeFigure} and confirms there is no COO marking visible.`;
  }

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
          slug: slugify(entry.name.replace(".txt", "")),
          fullPath: path.join(folderPath, entry.name)
        });
      }
    }
  }

  return files;
}

function isGeneralReference(file) {
  const generalRefs = [
    "accessory-production",
    "coo-guide",
    "vendor-codes",
    "early-bird-certificate-package"
  ];

  return file.folder === "references" && generalRefs.some(ref => file.slug.includes(ref));
}

function isFigureRelated(file, activeFigure) {
  if (!activeFigure) return false;
  return file.slug.includes(activeFigure);
}

function isAccessoryRelated(file, activeFigure) {
  if (!activeFigure) return false;

  const map = {
    "jawa": ["jawa-blaster", "jawa-cloak", "jawa-vinyl-cape"],
    "luke-skywalker": ["double-telescoping-lightsaber", "telescoping-lightsaber", "lightsaber"],
    "darth-vader": ["lightsaber", "darth-vader-cape"],
    "obi-wan-kenobi": ["lightsaber", "ben-obi-wan-kenobi-cape", "obi-wan-kenobi-cape"]
  };

  const related = map[activeFigure] || [];
  return related.some(item => file.slug.includes(item));
}

async function buildContext(message, history, activeFigure) {
  const baseDir = path.join(process.cwd(), "data");
  const files = await collectFiles(baseDir);

  let candidateFiles = files;

  if (activeFigure) {
    candidateFiles = files.filter(
      file =>
        isFigureRelated(file, activeFigure) ||
        isAccessoryRelated(file, activeFigure) ||
        isGeneralReference(file)
    );
  }

  let context = "";

  for (const file of candidateFiles) {
    const content = await safeReadFile(file.fullPath);
    if (content.trim()) {
      context += `\nFILE: ${file.folder}/${file.name}\n${content}\n`;
    }
  }

  return context.slice(0, 18000);
}

function buildTranscript(history) {
  if (!history.length) return "None";

  return history
    .map(m => `${m.role === "user" ? "User" : "VF-CB"}: ${m.content}`)
    .join("\n\n");
}

function extractOpenAIReply(data) {
  if (typeof data?.output_text === "string" && data.output_text.trim()) {
    return data.output_text.trim();
  }

  if (Array.isArray(data?.output)) {
    const chunks = [];

    for (const item of data.output) {
      if (!Array.isArray(item?.content)) continue;

      for (const part of item.content) {
        if (typeof part?.text === "string" && part.text.trim()) {
          chunks.push(part.text.trim());
        }
      }
    }

    const joined = chunks.join("\n").trim();
    if (joined) return joined;
  }

  return "No response";
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

    if (!process.env.OPENAI_API_KEY) {
      return res.status(500).json({ error: "OPENAI_API_KEY is not configured" });
    }

    const cleanHistory = sanitiseHistory(history);
    const activeFigure = detectActiveFigure(message, cleanHistory);
    const expandedMessage = expandShortReply(message, activeFigure);
    const context = await buildContext(expandedMessage, cleanHistory, activeFigure);
    const transcript = buildTranscript(cleanHistory);

    const systemPrompt = `
You are VF-CB, a vintage Star Wars figure and accessory expert.

Default assumption:
The user means the original vintage Star Wars toy line from 1977 to 1985.

Important wording rules:
- Do NOT default to "Kenner"
- Only mention specific companies when relevant
- Collectors may casually call both vinyl and cloth versions a "cape"

Critical accuracy rules:
1. Only state claims like "most common", "rarer", "typical", or "usually found" if clearly supported by the supplied information
2. If the supplied information does not confirm something, do not guess
3. Avoid stating obvious physical traits unless they add real identification value

Answer style:
- Speak like an experienced collector
- Be clear, direct, and practical
- Prioritise useful identification insight over general description

Collector logic:
1. Always prioritise the most useful identifier first
2. For Jawa identification, start with:
   - vinyl cape
   - cloth cape / cloak
   - or no body covering present
3. If cloth Jawa, next useful checks are:
   - COO / leg markings
   - hood size and shape
   - stitching and construction
   - then other figure traits
4. For incomplete loose figures, still help identify them using figure traits even if accessories are missing
5. Make it clear that COO alone is not enough to confirm a figure's origins
6. If an active figure has already been established in the recent conversation, stay locked on that figure unless the user clearly changes subject
7. Do not switch to another figure just because a word such as cape, vinyl, cloth, hood, or blaster could also apply elsewhere
8. Do not restart the conversation or reintroduce yourself again unless the user clearly starts a new topic

Never:
- invent information
- assume rarity or frequency
- state "most common" without explicit support
- mention files, context, prompts, or system internals

Optional personality:
You may add one short polite droid-like opening line occasionally.
Do not roleplay as a named character.

Goal:
Sound like a knowledgeable collector helping another collector identify or understand something, using only grounded, reliable information.
`;

    const userPrompt = `
Current user message:
${message}

Expanded meaning:
${expandedMessage}

Active figure/topic:
${activeFigure || "None clearly established"}

Recent conversation:
${transcript}

Supporting information:
${context}

Instructions:
- Use the expanded meaning if the current message is short
- Stay on the active figure/topic
- Do not switch to another figure unless the user clearly does so
- Do not restart or introduce yourself again
- Move the identification forward by asking or answering the next useful step
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
            content: userPrompt
          }
        ],
        max_output_tokens: 600
      })
    });

    const data = await response.json();

    if (!response.ok) {
      console.error("OpenAI error:", data);
      return res.status(500).json({
        error: "OpenAI API error",
        details: data
      });
    }

    return res.status(200).json({
      reply: extractOpenAIReply(data)
    });
  } catch (err) {
    console.error(err);
    return res.status(500).json({
      error: "Server error",
      details: err.message
    });
  }
}
