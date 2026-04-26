import fs from "fs/promises";
import path from "path";

function normaliseText(text) {
  return String(text || "").toLowerCase().trim();
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

function buildConversationText(message, history = []) {
  return [
    ...history.map((m) => m.content || ""),
    message || "",
  ].join(" ").toLowerCase();
}

function looksLikeJawaNoCooMarking(message) {
  const lower = normaliseText(message);

  return (
    lower.includes("gmfgi") ||
    lower.includes("g.m.f.g.i") ||
    lower.includes("cmfg") ||
    (lower.includes("1977") && (lower.includes("hard to tell") || lower.includes("just says") || lower.includes("looks like")))
  );
}

function getDeterministicReply(message, history = [], activeFigure = "") {
  const lower = normaliseText(message);
  const convo = buildConversationText(message, history);

  if (activeFigure === "jawa") {
    if (
      lower === "help me identify a jawa" ||
      lower === "help me identify my jawa" ||
      lower === "can you help me identify a jawa" ||
      lower === "can you help me identify my jawa" ||
      lower === "help me identify a jawa please" ||
      lower === "help me identify my jawa please"
    ) {
      return `Yes I can do that — let's start with the cape.

Which of these does your Jawa have?

1. Vinyl cape - smooth plastic
2. Cloth cloak - fabric
3. Or neither. Just a naked figure

Just tell me: vinyl, cloth, or missing cloak.
Or you can reply with 1, 2 or 3.`;
    }

    if (lower === "1" || lower === "vinyl") {
      return `Good — that means you have the early vinyl cape version.

Next step:
Check the COO marking on the legs.

Then we confirm it properly using:
• body sculpt
• plastic colour
• paint details
• and the correct blaster pairing

Do not rely on COO alone — mould, paint colour, plastic colour and figure assembly traits are also needed to confirm origin.

What does the leg marking say?`;
    }

    if (lower === "2" || lower === "cloth") {
      return `Good — so we're dealing with a cloth cloak Jawa.

Next step:
Check the COO marking on the legs.

After that, the next useful things are:
• hood size and shape
• stitching / construction
• eye colour
• bandolier shape and tone
• and whether the blaster is present

Do not rely on COO alone — mould, paint colour, plastic colour and figure assembly traits are also needed to confirm origin.

What does the leg marking say?`;
    }

    if (
      lower === "3" ||
      lower === "no cape" ||
      lower === "missing cloak" ||
      lower === "naked"
    ) {
      return `Right — so your Jawa is missing its cape, what collectors would usually call a naked figure.

That’s common, so we identify it from the figure itself.

Next step:
Check the COO marking on the legs.

Then we confirm it using:
• mould / sculpt
• plastic colour
• eye paint
• bandolier shape and tone
• and any remaining accessories

Do not rely on COO alone — mould, paint colour, plastic colour and figure assembly traits are also needed to confirm origin.

What does the leg marking say?`;
    }

    if (lower.includes("what's coo") || lower.includes("whats coo") || lower === "coo") {
      return `COO means Country of Origin.

That is the country marking usually found on the legs of vintage figures, such as Hong Kong or Taiwan.

On Jawas, COO is a very useful starting point — but not enough on its own.

To confirm a Jawa properly, you also need to check:
• mould / sculpt
• eye colour
• plastic colour
• bandolier shape and tone
• and cloak or blaster pairing if present`;
    }

    if (looksLikeJawaNoCooMarking(message) || convo.includes("jawa") && looksLikeJawaNoCooMarking(message)) {
      return `If you can't see Hong Kong on the leg, you must have a Kader China variant.

It will have just one line of text reading:
© G.M.F.G.I. 1977

That stands for General Mills Fun Group Incorporated, with 1977 being the year the figure was originally licensed.

KADER (CHINA) NCOO should be:

• Rectangular dark brown bandolier
• Round yellow eyes
• Smooth cloth cloak

or

• Rectangular, very dark brown bandolier
• Round yellow eyes
• Smooth cloth cloak

Paired with an M2 Kader Jawa Blaster — the one with the short bump.

There are two variants within this Kader China NCOO version.
The difference is the size of the copyright text on the back of the leg.

If you want, next send:
• a close photo of the back of the legs
• a front photo of the figure
• and the cloak hood if present

That will let me narrow down which of the two Kader China NCOO variants it is.`;
    }
  }

  return null;
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
          slug: entry.name.replace(/\.txt$/i, "").toLowerCase(),
          fullPath: path.join(folderPath, entry.name),
        });
      }
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

    const historyOnly = incomingMessages
      .slice(0, -1)
      .filter((m) => m.role === "user" || m.role === "assistant");

    const activeFigure = detectActiveFigure(lastUserMessage, historyOnly);

    const deterministicReply = getDeterministicReply(lastUserMessage, historyOnly, activeFigure);
    if (deterministicReply) {
      return res.status(200).json({ reply: deterministicReply });
    }

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

Collectors may casually call both vinyl and cloth versions a cape.

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
${lastUserMessage}
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
        temperature: 0.2,
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
