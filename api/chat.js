const fs = require("fs");
const path = require("path");

const DATA_ROOT = path.join(process.cwd(), "data");
const MODEL = process.env.ANTHROPIC_MODEL || "claude-haiku-4-5-20251001";

const URLS = {
  jawaBlaster: "https://www.variantvillain.com/accessory-guide/jawa-blaster/",
  jawaCloak: "https://www.variantvillain.com/accessory-guide/jawa-cloak/",
  jawaVinylCape: "https://www.variantvillain.com/accessory-guide/jawa-vinyl-cape/",
  jawaFigure: "https://www.variantvillain.com/characters/sw/jawa/"
};

const IMAGE_MAP = {
  jawaBlaster: {
    title: "Jawa Blaster Reference",
    url: "https://www.variantvillain.com/wp-content/uploads/2021/12/JawaBlaster_000.jpg",
    caption: "Compare mould shape, rear bump length, plastic colour and detail sharpness."
  },
  jawaVinylCape: {
    title: "Jawa Vinyl Cape Authentication Reference",
    url: "/public/images/jawa-vinyl-cape-01.png",
    caption: "Compare cape shape, surface texture on both sides, colour and signs of a cut-down Ben cape."
  }
};

const KNOWN_ENTITIES = [
  { keys: ["jawa"], slug: "jawa" },
  { keys: ["luke skywalker", "luke"], slug: "luke-skywalker" },
  { keys: ["darth vader", "vader"], slug: "darth-vader" },
  { keys: ["ben obi-wan kenobi", "obi-wan", "obi wan", "ben kenobi", "ben"], slug: "ben-obi-wan-kenobi" },
  { keys: ["princess leia", "leia organa", "leia"], slug: "princess-leia-organa" },
  { keys: ["han solo", "han"], slug: "han-solo" },
  { keys: ["chewbacca", "chewie"], slug: "chewbacca" },
  { keys: ["stormtrooper", "storm trooper"], slug: "stormtrooper" },
  { keys: ["r2-d2", "r2d2", "r2"], slug: "r2-d2" },
  { keys: ["c-3po", "c3po", "3po"], slug: "c-3po" },
  { keys: ["death squad commander"], slug: "death-squad-commander" },
  { keys: ["sand people", "sand person", "tusken"], slug: "sand-people" }
];

const ACCESSORY_ALIASES = [
  { keys: ["blaster", "gun", "pistol", "weapon", "accessory", "accessories", "laser", "laser gun", "laser pistol", "ray", "ray gun", "shooter", "zapper", "pew", "pew pew", "sidearm"], slug: "blaster" },
  { keys: ["lightsaber", "light saber", "sabre", "saber"], slug: "lightsaber" },
  { keys: ["cloak", "cloth cloak"], slug: "cloak" },
  { keys: ["vinyl cape"], slug: "vinyl-cape" },
  { keys: ["cape"], slug: "cape" },
  { keys: ["bowcaster", "bow caster"], slug: "bowcaster" },
  { keys: ["gaffi", "gaffi stick", "gaderffii", "gaderffi"], slug: "gaderffi-stick" }
];

function normalise(text) {
  return String(text || "")
    .toLowerCase()
    .replace(/[^a-z0-9\s\-]/g, " ")
    .replace(/\s+/g, " ")
    .trim();
}

function includesAny(t, keys) {
  return keys.some((key) => t.includes(key));
}

function detectEntity(message) {
  const t = normalise(message);
  for (const entity of KNOWN_ENTITIES) {
    if (includesAny(t, entity.keys)) return entity.slug;
  }
  return null;
}

function detectAccessory(message) {
  const t = normalise(message);
  for (const acc of ACCESSORY_ALIASES) {
    if (includesAny(t, acc.keys)) return acc.slug;
  }
  return null;
}

function detectIntent(message) {
  const t = normalise(message);
  const accessory = detectAccessory(t);

  if (accessory) return "accessory";
  if (t.includes("coo") || t.includes("country of origin") || t.includes("leg mark") || t.includes("leg marking")) return "figure";
  if (t.includes("id") || t.includes("identify") || t.includes("variant") || t.includes("figure")) return "figure";

  return "unknown";
}

function lastAssistant(history) {
  const items = Array.isArray(history) ? history : [];
  for (let i = items.length - 1; i >= 0; i--) {
    if (items[i]?.role === "assistant") return String(items[i].content || "");
  }
  return "";
}

function inferState(history) {
  const last = lastAssistant(history).toLowerCase();

  if (last.includes("can you identify it against the reference image")) return "jawa-blaster-image";
  if (last.includes("does yours sink or float")) return "jawa-blaster-float";
  if (last.includes("what colour does yours look like") || last.includes("now check the colour")) return "jawa-blaster-colour";
  if (last.includes("did you want help with") && last.includes("jawa blaster")) return "jawa-clarify";

  return null;
}

function fileExists(relPath) {
  return fs.existsSync(path.join(process.cwd(), relPath));
}

function readRel(relPath) {
  const fullPath = path.join(process.cwd(), relPath);
  try {
    return fs.readFileSync(fullPath, "utf8");
  } catch {
    return "";
  }
}

function walkFiles(dir) {
  const results = [];
  if (!fs.existsSync(dir)) return results;

  for (const item of fs.readdirSync(dir, { withFileTypes: true })) {
    const fullPath = path.join(dir, item.name);
    if (item.isDirectory()) {
      results.push(...walkFiles(fullPath));
    } else if (/\.(txt|json|md)$/i.test(item.name)) {
      results.push(fullPath);
    }
  }

  return results;
}

function rel(filePath) {
  return path.relative(process.cwd(), filePath).replace(/\\/g, "/");
}

function findRelevantFile(message) {
  const entity = detectEntity(message);
  const accessory = detectAccessory(message);
  const intent = detectIntent(message);

  const direct = [];

  if (entity && intent === "figure") {
    direct.push(`data/figures/${entity}-reference.txt`);
  }

  if (entity === "jawa" && accessory === "blaster") direct.push("data/accessories/jawa-blaster.txt");
  if (entity === "jawa" && accessory === "cloak") direct.push("data/accessories/jawa-cloak.txt");
  if (entity === "jawa" && accessory === "vinyl-cape") direct.push("data/accessories/jawa-vinyl-cape.txt");
  if (entity === "chewbacca" && accessory === "bowcaster") direct.push("data/accessories/chewbacca-bowcaster.txt");
  if (entity === "stormtrooper" && accessory === "blaster") direct.push("data/accessories/imperial-blaster.txt");
  if (entity === "leia" && accessory === "blaster") direct.push("data/accessories/leia-blaster.txt");

  if (accessory === "lightsaber") direct.push("data/accessories/lightsaber.txt");
  if (accessory === "blaster") direct.push("data/accessories/rebel-blaster.txt", "data/accessories/imperial-blaster.txt");

  const existingDirect = direct.filter(fileExists);
  if (existingDirect.length) return existingDirect.slice(0, 4);

  const all = walkFiles(DATA_ROOT);
  const t = normalise(message);
  const words = t.split(" ").filter(Boolean);

  return all
    .map((filePath) => {
      const r = rel(filePath).toLowerCase();
      let score = 0;
      for (const word of words) {
        if (r.includes(word)) score += 5;
      }
      if (entity && r.includes(entity)) score += 25;
      if (accessory && r.includes(accessory)) score += 25;
      if (intent === "figure" && r.includes("/figures/")) score += 10;
      if (intent === "accessory" && r.includes("/accessories/")) score += 10;
      return { filePath, score };
    })
    .filter((x) => x.score > 0)
    .sort((a, b) => b.score - a.score)
    .slice(0, 4)
    .map((x) => rel(x.filePath));
}

function sourceBlock(files) {
  return files
    .map((file) => {
      const text = readRel(file).slice(0, 7000);
      return `SOURCE FILE: ${file}\n${text}`;
    })
    .join("\n\n---\n\n");
}

function jawaBlasterStart() {
  return {
    reply: `Ok — compare your blaster with this reference.

Check:
• mould shape
• rear bump length
• plastic colour
• detail sharpness

Can you identify it against the reference image?

Reply with:

1 Yes
2 No
3 Not sure`,
    images: [IMAGE_MAP.jawaBlaster]
  };
}

function jawaBlasterFloatQuestion() {
  return {
    reply: `Next check: float test.

• If it sinks, treat it as a reproduction
• If it floats, it may be original

Important:
Modern reproductions can float, so this is not proof.

Does yours sink or float?

Reply with:

1 Float
2 Sink`,
    images: []
  };
}

function jawaBlasterColourQuestion() {
  return {
    reply: `Good. Since it floats, next check the colour.

Most original Jawa blasters are dark blue or black-blue tones.

What colour does yours look like?

Reply with:

1 Dark blue / black-blue
2 Black
3 Grey
4 Silver
5 Not sure`,
    images: []
  };
}

function jawaBlasterColourReply(message) {
  const t = normalise(message);

  if (t === "1" || t.includes("dark blue") || t.includes("black blue") || t.includes("blue")) {
    return {
      reply: `That is the safest colour range for most original Jawa blasters.

Known original colours include:
• black-blue, semi-translucent blueish
• black-blue, semi-translucent greenish
• black-blue, semi-translucent greyish
• dark-blue, translucent blueish
• dark-blue, translucent greenish
• dark-blue, semi-translucent greyish

Still compare the exact mould shape, rear bump and detail sharpness against Variant Villain:
${URLS.jawaBlaster}`,
      images: []
    };
  }

  if (t === "2" || t.includes("black")) {
    return {
      reply: `Black needs caution.

It could be:
• a reproduction
• a modern accessory
• a very dark blue original being mistaken for black
• or, much less commonly, a Brazilian Glasslite black blaster

Do not call it original based on colour alone. Compare the mould exactly against the known examples:
${URLS.jawaBlaster}`,
      images: []
    };
  }

  if (t === "3" || t.includes("grey") || t.includes("gray")) {
    return {
      reply: `Grey pieces need extra caution.

Grey is a very common reproduction colour for Jawa blasters.

There are rare silver Glasslite versions, but they are extremely uncommon and should not be assumed.

Best next step: compare it closely with the full Variant Villain guide:
${URLS.jawaBlaster}`,
      images: []
    };
  }

  if (t === "4" || t.includes("silver")) {
    return {
      reply: `Silver is unusual.

There is a rare silver Jawa blaster associated with the Brazilian Glasslite figure, but it is extremely uncommon.

Do not assume it is Glasslite without matching the mould and provenance carefully.

Use the full reference:
${URLS.jawaBlaster}`,
      images: []
    };
  }

  return {
    reply: `If you are not sure on colour, compare it in natural light against the known Variant Villain examples.

Known original colour families include dark-blue / black-blue tones, plus rare Glasslite black and silver versions.

Full reference:
${URLS.jawaBlaster}`,
    images: []
  };
}

function handleDeterministic(message, history) {
  const t = normalise(message);
  const state = inferState(history);
  const entity = detectEntity(message);
  const accessory = detectAccessory(message);
  const intent = detectIntent(message);

  if (state === "jawa-blaster-image") {
    return jawaBlasterFloatQuestion();
  }

  if (state === "jawa-blaster-float") {
    if (t === "2" || t.includes("sink") || t.includes("sinks") || t.includes("sank")) {
      return { reply: "If it sinks, treat it as a reproduction.", images: [] };
    }

    if (t === "1" || t.includes("float") || t.includes("floats")) {
      return jawaBlasterColourQuestion();
    }

    return { reply: "Please reply with 1 for float, or 2 for sink.", images: [] };
  }

  if (state === "jawa-blaster-colour") {
    return jawaBlasterColourReply(message);
  }

  if (state === "jawa-clarify") {
    if (t === "1") return jawaBlasterStart();
    if (t === "2") return null;
    if (t === "3") {
      return {
        reply: `For Jawa cloak or cape checks, use the Variant Villain guides:

Cloth cloak:
${URLS.jawaCloak}

Vinyl cape:
${URLS.jawaVinylCape}

Ask me a specific cloak or cape question and I’ll use the local reference files to help.`,
        images: []
      };
    }
    return { reply: "Please reply with 1, 2 or 3.", images: [] };
  }

  if (entity === "jawa" && accessory === "blaster") {
    return jawaBlasterStart();
  }

  if (entity === "jawa" && intent === "unknown") {
    return {
      reply: `I’m not sure which Jawa area you mean.

Did you want help with:

1 Jawa blaster (weapon)
2 Jawa figure
3 Jawa cloak / cape

Reply with 1, 2 or 3.`,
      images: []
    };
  }

  return null;
}

function buildSystemPrompt(files, message) {
  return `You are VF-CB, a Vintage Kenner Star Wars figure and accessory identification assistant.

Use the supplied local reference files as the source of truth.

Rules:
- Ask ONE question at a time.
- Prefer numbered replies.
- Keep answers concise.
- Do not repeat the same line twice.
- Do not say "Try asking about a Jawa figure or blaster" unless no relevant file exists.
- If the user says "id jawa", assume they mean the Jawa figure.
- If the user includes accessory words, treat it as an accessory request.
- If uncertain, ask a useful clarification question.
- Never claim something is original unless the evidence is strong.
- For valuable items, recommend confirmation from experienced collector groups.

User message:
${message}

Reference files:
${sourceBlock(files)}

Return ONLY valid JSON:
{
  "reply": "message to user",
  "images": []
}`;
}

async function callClaude(systemPrompt, history, message) {
  const apiKey = process.env.ANTHROPIC_API_KEY;
  if (!apiKey) throw new Error("Missing ANTHROPIC_API_KEY");

  const messages = [];
  const cleanHistory = Array.isArray(history) ? history.slice(-8) : [];

  for (const item of cleanHistory) {
    if (!item || !item.role || !item.content) continue;
    if (item.role !== "user" && item.role !== "assistant") continue;
    messages.push({
      role: item.role,
      content: String(item.content).slice(0, 1500)
    });
  }

  messages.push({ role: "user", content: message });

  const response = await fetch("https://api.anthropic.com/v1/messages", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "x-api-key": apiKey,
      "anthropic-version": "2023-06-01"
    },
    body: JSON.stringify({
      model: MODEL,
      max_tokens: 700,
      temperature: 0.1,
      system: systemPrompt,
      messages
    })
  });

  const data = await response.json();

  if (!response.ok) {
    throw new Error(data?.error?.message || "Anthropic API error");
  }

  return data?.content?.[0]?.text || "";
}

function parseJson(text) {
  try {
    return JSON.parse(text);
  } catch {
    const start = text.indexOf("{");
    const end = text.lastIndexOf("}");
    if (start >= 0 && end > start) {
      try {
        return JSON.parse(text.slice(start, end + 1));
      } catch {
        return null;
      }
    }
    return null;
  }
}

module.exports = async function handler(req, res) {
  if (req.method !== "POST") {
    res.status(405).json({ error: "Method not allowed" });
    return;
  }

  try {
    const message = String(req.body?.message || "").trim();
    const history = Array.isArray(req.body?.history) ? req.body.history : [];

    if (!message) {
      res.status(400).json({ error: "Missing message" });
      return;
    }

    const deterministic = handleDeterministic(message, history);
    if (deterministic) {
      res.status(200).json({
        reply: deterministic.reply,
        images: deterministic.images || []
      });
      return;
    }

    const files = findRelevantFile(message);

    if (!files.length) {
      res.status(200).json({
        reply: `I’m not sure what you want to identify yet.

Tell me the figure or accessory, for example:

• Jawa figure
• Jawa blaster
• Luke lightsaber
• Stormtrooper blaster`,
        images: []
      });
      return;
    }

    const prompt = buildSystemPrompt(files, message);
    const text = await callClaude(prompt, history, message);
    const parsed = parseJson(text);

    if (!parsed || !parsed.reply) {
      res.status(200).json({
        reply: text || "I found the relevant file, but could not format a clean answer.",
        images: []
      });
      return;
    }

    res.status(200).json({
      reply: parsed.reply,
      images: Array.isArray(parsed.images) ? parsed.images : []
    });
  } catch (err) {
    console.error(err);
    res.status(500).json({ error: err.message || "Server error" });
  }
};
