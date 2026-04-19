import fs from "fs";
import path from "path";

function readJsonSafe(filePath, fallback = null) {
  try {
    if (!fs.existsSync(filePath)) return fallback;
    return JSON.parse(fs.readFileSync(filePath, "utf-8"));
  } catch {
    return fallback;
  }
}

function loadAllJsonFiles(dirPath) {
  if (!fs.existsSync(dirPath)) return [];
  const files = fs.readdirSync(dirPath).filter((f) => f.endsWith(".json"));
  const out = [];
  for (const file of files) {
    const parsed = readJsonSafe(path.join(dirPath, file));
    if (parsed) out.push(parsed);
  }
  return out;
}

function loadFigureData() {
  return loadAllJsonFiles(path.join(process.cwd(), "data", "figures"));
}

function loadAccessoryData() {
  return loadAllJsonFiles(path.join(process.cwd(), "data", "accessories"));
}

function loadAccessoryVariants() {
  return loadAllJsonFiles(path.join(process.cwd(), "data", "variants"));
}

function loadReferences() {
  return loadAllJsonFiles(path.join(process.cwd(), "data", "references")).flat();
}

function normalise(text = "") {
  return String(text).toLowerCase().trim();
}

function includesAny(text, values = []) {
  const t = normalise(text);
  return values.some((v) => t.includes(normalise(v)));
}

function pickRelevantFigure(text, figures) {
  const t = normalise(text);
  for (const fig of figures) {
    const aliases = Array.isArray(fig.aliases) ? fig.aliases : [];
    const names = [fig.display_name, fig.full_name, fig.subtitle].filter(Boolean);
    if (includesAny(t, [...aliases, ...names])) return fig;
  }
  return null;
}

function pickRelevantAccessory(text, accessories) {
  const t = normalise(text);
  for (const acc of accessories) {
    const names = [
      acc.display_name,
      acc.description_short,
      ...(Array.isArray(acc.aliases) ? acc.aliases : [])
    ].filter(Boolean);
    if (includesAny(t, names)) return acc;
  }
  return null;
}

function resolveConversationContext(history = [], figures = [], accessories = []) {
  let currentFigure = null;
  let currentAccessory = null;

  for (const msg of history) {
    if (!msg || msg.role !== "user" || !msg.content) continue;
    const foundFigure = pickRelevantFigure(msg.content, figures);
    const foundAccessory = pickRelevantAccessory(msg.content, accessories);

    if (foundFigure) currentFigure = foundFigure;
    if (foundAccessory) currentAccessory = foundAccessory;

    // Lightweight collector context handling for common follow-up phrases
    const text = normalise(msg.content);

    if (currentFigure?.id === "figure_luke_skywalker_farmboy") {
      if (["kader", "unitoy", "smile", "taiwan", "trilogo", "handheld saber", "bespin saber"].some((k) => text.includes(k))) {
        currentFigure = currentFigure;
      }
    }
  }

  return { currentFigure, currentAccessory };
}

function buildReferenceBlock({ currentFigure, currentAccessory, variants, references }) {
  let lines = [];

  if (currentFigure) {
    lines.push(`CURRENT FIGURE CONTEXT`);
    lines.push(`Name: ${currentFigure.full_name || currentFigure.display_name}`);
    if (currentFigure.description_short) lines.push(`Summary: ${currentFigure.description_short}`);
    if (Array.isArray(currentFigure.notes_general) && currentFigure.notes_general.length) {
      lines.push(`Notes:`);
      for (const note of currentFigure.notes_general) lines.push(`- ${note}`);
    }
    lines.push("");
  }

  if (currentAccessory) {
    lines.push(`CURRENT ACCESSORY CONTEXT`);
    lines.push(`Name: ${currentAccessory.display_name}`);
    if (currentAccessory.description_short) lines.push(`Summary: ${currentAccessory.description_short}`);
    if (Array.isArray(currentAccessory.notes_general) && currentAccessory.notes_general.length) {
      lines.push(`Notes:`);
      for (const note of currentAccessory.notes_general) lines.push(`- ${note}`);
    }
    lines.push("");
  }

  const relevantVariants = [];
  if (currentFigure?.id === "figure_luke_skywalker_farmboy") {
    for (const variant of variants) {
      if (variant.id === "accvar_dt_lightsaber_m2_yellow" ||
          variant.id === "accvar_st_lightsaber_m1_yellow" ||
          variant.id === "accvar_handheld_lightsaber_m3_yellow") {
        relevantVariants.push(variant);
      }
    }
  }

  if (relevantVariants.length) {
    lines.push(`RELEVANT ACCESSORY VARIANTS`);
    for (const v of relevantVariants) {
      lines.push(`- ${v.variant_name}`);
      if (v.quick_id) lines.push(`  Quick ID: ${v.quick_id}`);
      if (Array.isArray(v.key_traits) && v.key_traits.length) {
        lines.push(`  Traits: ${v.key_traits.join(", ")}`);
      }
      if (Array.isArray(v.notes) && v.notes.length) {
        lines.push(`  Notes: ${v.notes.join(" | ")}`);
      }
    }
    lines.push("");
  }

  if (references.length) {
    lines.push(`REFERENCE SOURCES`);
    for (const ref of references.slice(0, 12)) {
      lines.push(`- ${ref.title}: ${ref.url}`);
    }
  }

  return lines.join("\n").trim();
}

export default async function handler(req, res) {
  if (req.method !== "POST") {
    return res.status(405).json({ error: "Method not allowed" });
  }

  try {
    const { message, history = [] } = req.body || {};

    if (!message || typeof message !== "string") {
      return res.status(400).json({ error: "Message is required" });
    }

    const figures = loadFigureData();
    const accessories = loadAccessoryData();
    const variants = loadAccessoryVariants();
    const references = loadReferences();

    const safeHistory = Array.isArray(history)
      ? history
          .filter((m) => m && typeof m.content === "string" && (m.role === "user" || m.role === "assistant"))
          .slice(-12)
      : [];

    const conversationContext = resolveConversationContext(
      [...safeHistory, { role: "user", content: message }],
      figures,
      accessories
    );

    const referenceBlock = buildReferenceBlock({
      ...conversationContext,
      variants,
      references,
    });

    const systemPrompt = `
You are VF-CB, the Vintage Figures Chat Bot.

Your job:
- Continue the conversation naturally.
- Use prior chat context when the user follows up.
- Do not ask the user to repeat the figure name if it is obvious from the conversation.
- Answer like a knowledgeable vintage Kenner Star Wars collector.
- Keep the first answer concise.
- Expand only if asked.
- Be honest when the data is uncertain.
- Never invent COO matches or accessory pairings.
- If the user asks a follow-up like "what accessories did they come with?" and the previous turn already established the figures, answer that directly.
- If the user refers to "they", "those", "that one", "the early bird figures", use the prior conversation context.

Known app data:
${referenceBlock || "No matched local reference data yet."}
`.trim();

    const anthropicMessages = [
      ...safeHistory.map((m) => ({
        role: m.role,
        content: m.content,
      })),
      {
        role: "user",
        content: message,
      },
    ];

    const response = await fetch("https://api.anthropic.com/v1/messages", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "x-api-key": process.env.ANTHROPIC_API_KEY,
        "anthropic-version": "2023-06-01",
      },
      body: JSON.stringify({
        model: "claude-haiku-4-5-20251001",
        max_tokens: 700,
        system: systemPrompt,
        messages: anthropicMessages,
      }),
    });

    const data = await response.json();

    if (!response.ok) {
      return res.status(response.status).json({
        error: data?.error?.message || "Anthropic API error",
        raw: data,
      });
    }

    const reply = data?.content?.[0]?.text || "No response";

    return res.status(200).json({
      reply,
      context: {
        figure: conversationContext.currentFigure?.id || null,
        accessory: conversationContext.currentAccessory?.id || null,
      },
    });
  } catch (error) {
    return res.status(500).json({ error: error.message || "Unknown server error" });
  }
}
