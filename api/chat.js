import fs from "fs/promises";
import path from "path";

function normaliseText(text) {
  return String(text || "").toLowerCase();
}

function sanitiseHistory(history) {
  if (!Array.isArray(history)) return [];
  return history
    .filter(
      (m) =>
        m &&
        typeof m.content === "string" &&
        (m.role === "user" || m.role === "assistant")
    )
    .slice(-12);
}

function detectActiveFigure(message, history = []) {
  const combined = [
    ...history.map((m) => m.content || ""),
    message || "",
  ].join(" ");

  const lower = normaliseText(combined);

  if (lower.includes("jawa")) return "jawa";
  if (lower.includes("luke")) return "luke-skywalker";
  if (lower.includes("leia")) return "princess-leia-organa";
  if (lower.includes("chewbacca") || lower.includes("chewie") || lower.includes("chewy")) return "chewbacca";
  if (lower.includes("r2-d2") || lower.includes("r2d2") || lower.includes("r2")) return "r2-d2";
  if (lower.includes("vader")) return "darth-vader";
  if (lower.includes("obi-wan") || lower.includes("obi wan") || lower.includes("ben kenobi")) return "obi-wan-kenobi";

  return "";
}

function expandShortReply(message, activeFigure) {
  const m = String(message || "").trim().toLowerCase();

  if (!activeFigure) return message;

  const map = {
    "1": `User is identifying a ${activeFigure} and says it has a vinyl cape.`,
    "2": `User is identifying a ${activeFigure} and says it has a cloth cloak or cloth cape.`,
    "3": `User is identifying a ${activeFigure} and says it has no cape or cloak present.`,
    "vinyl": `User is identifying a ${activeFigure} and says it has a vinyl cape.`,
    "cloth": `User is identifying a ${activeFigure} and says it has a cloth cloak or cloth cape.`,
    "no cape": `User is identifying a ${activeFigure} and says it has no cape or cloak present.`,
    "missing cloak": `User is identifying a ${activeFigure} and says it has no cape or cloak present.`,
    "naked": `User is identifying a ${activeFigure} and says it has no cape or cloak present.`,
    "no blaster": `User is identifying a ${activeFigure} and says the blaster is missing.`,
    "hong kong": `User is identifying a ${activeFigure} and says the COO marking is Hong Kong.`,
    "taiwan": `User is identifying a ${activeFigure} and says the COO marking is Taiwan.`,
    "china": `User is identifying a ${activeFigure} and says the COO marking is China.`,
    "macau": `User is identifying a ${activeFigure} and says the COO marking is Macau.`,
    "no coo": `User is identifying a ${activeFigure} and says there is no COO marking visible.`,
  };

  return map[m] || message;
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
        slug: entry.name.replace(/\.txt$/i, "").toLowerCase(),
        fullPath: path.join(folderPath, entry.name),
      });
    }
  }

  return files;
}

function fileIsRelevant(file, activeFigure) {
  if (!activeFigure) return true;

  const generalRefs = [
    "coo-guide",
    "vendor-codes",
    "accessory-production",
    "early-bird-certificate-package",
    "collector_glossary",
  ];

  if (file.folder === "references" && generalRefs.some((ref) => file.slug.includes(ref))) {
    return true;
  }

  if (file.slug.includes(activeFigure)) return true;

  const accessoryMap = {
    "jawa": ["jawa-blaster", "jawa-cloak", "jawa-vinyl-cape"],
    "luke-skywalker": ["double-telescoping-lightsaber", "telescoping-lightsaber", "lightsaber"],
    "darth-vader": ["darth-vader-cape", "lightsaber"],
    "obi-wan-kenobi": ["ben-obi-wan-kenobi-cape", "obi-wan-kenobi-cape", "lightsaber"],
  };

  const related = accessoryMap[activeFigure] || [];
  return related.some((item) => file.slug.includes(item));
}

async function buildContext(activeFigure) {
  const baseDir = path.join(process.cwd(), "data");
  const files = await collectFiles(baseDir);

  const relevantFiles = files.filter((file) => fileIsRelevant(file, activeFigure)).slice(0, 20);

  let context = "";

  for (const file of relevantFiles) {
    const content = await safeReadFile(file.fullPath);
    if (content.trim()) {
      context += `\nFILE: ${file.folder}/${file.name}\n${content}\n`;
    }
  }

  return context.slice(0, 18000);
}

function buildMessagesFromFrontend(body) {
  if (Array.isArray(body.messages)) {
    return body.messages.filter(
      (m) =>
        m &&
        typeof m.content === "string" &&
        (m.role === "user" || m.role === "assistant" || m.role === "system")
    );
  }

  const message = typeof body.message === "string" ? body.message : "";
  const history = sanitiseHistory(body.history);

  if (!message) return [];

  return [
    ...history,
    { role: "user", content: message },
  ];
}

export default async function handler(req, res) {
  try {
    if (req.method !== "POST") {
      return res.status(405).json({ error: "Method not allowed" });
    }

    if (!process.env.OPENAI_API_KEY) {
      return res.status(500).json({ error: "OPENAI_API_KEY is not configured" });
    }

    const body = req.body || {};
    const incomingMessages = buildMessagesFromFrontend(body);

    if (!incomingMessages.length) {
      return res.status(400).json({ error: "No valid chat input received" });
    }

    const lastUserMessage =
      [...incomingMessages].reverse().find((m) => m.role === "user")?.content || "";

    const historyOnly = incomingMessages.slice(0, -1).filter((m) => m.role === "user" || m.role === "assistant");
    const activeFigure = detectActiveFigure(lastUserMessage, historyOnly);
    const expandedUserMessage = expandShortReply(lastUserMessage, activeFigure);
    const context = await buildContext(activeFigure);

    const systemPrompt = `
You are VF-CB (Vintage Figures – Collector Bot).

You are an expert in vintage Star Wars figures and accessories from 1977 to 1985.

Style:
- Clear, calm, direct
- Sound like a knowledgeable collector
- Slightly formal is fine, but natural
- Ask one step at a time
- Do not mention being an AI

Core rules:
- Stay on the current figure unless the user clearly changes subject
- Do not switch characters just because words like cape, cloak, vinyl, hood, blaster, or saber could apply elsewhere
- Do not guess
- Do not state rarity or frequency unless clearly supported
- Do not rely on COO alone; mould, paint, plastic colour and assembly traits also matter

Jawa flow:
If the user is identifying a Jawa, start with:
1. Vinyl cape
2. Cloth cloak / cloth cape
3. No covering present / naked

Collectors may casually call both vinyl and cloth versions a cape.

If the user says no cape, missing cloak, naked, or 3:
- Keep the subject locked on Jawa
- Confirm the cape is missing
- Explain that this is common
- Move to the next step:
  check the COO marking on the legs
- Then explain that mould, paint, plastic colour and assembly traits are needed to confirm the figure

Do not restart the conversation or reintroduce yourself after the first turn.
Keep replies short and practical.
`;

    const messagesForOpenAI = [
      { role: "system", content: systemPrompt },
      ...historyOnly.map((m) => ({
        role: m.role,
        content: m.content,
      })),
      {
        role: "user",
        content: `
Current figure/topic: ${activeFigure || "not yet established"}

Supporting reference context:
${context}

Current user message:
${expandedUserMessage}
        `.trim(),
      },
    ];

    const response = await fetch("https://api.openai.com/v1/chat/completions", {
      method: "POST",
      headers: {
        Authorization: `Bearer ${process.env.OPENAI_API_KEY}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        model: "gpt-4o-mini",
        messages: messagesForOpenAI,
        temperature: 0.3,
      }),
    });

    const data = await response.json();

    if (!response.ok) {
      console.error("OpenAI error:", data);
      return res.status(500).json({
        error: "OpenAI API error",
        details: data,
      });
    }

    const reply = data?.choices?.[0]?.message?.content || "No response";

    return res.status(200).json({ reply });
  } catch (error) {
    console.error("SERVER ERROR:", error);
    return res.status(500).json({
      error: "Server error",
      details: error.message,
    });
  }
}
