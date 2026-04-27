const fs = require("fs");
const path = require("path");

const DATA_ROOT = path.join(process.cwd(), "data");
const FLOWS_ROOT = path.join(DATA_ROOT, "flows");
const MODEL = process.env.ANTHROPIC_MODEL || "claude-haiku-4-5-20251001";

const ACCESSORY_TERMS = {
  blaster: [
    "blaster", "gun", "pistol", "weapon", "laser", "laser gun", "laser pistol",
    "ray", "ray gun", "shooter", "zapper", "pew", "pew pew", "sidearm"
  ],
  lightsaber: ["lightsaber", "light saber", "saber", "sabre"],
  "vinyl-cape": ["vinyl cape", "vinyl"],
  "cloth-cloak": ["cloth cloak", "cloth", "cloak", "robe"],
  cape: ["cape"],
  bowcaster: ["bowcaster", "bow caster"],
  gaderffi: ["gaffi", "gaffi stick", "gaderffii", "gaderffi"]
};

const FIGURE_ALIASES = [
  { slug: "jawa", terms: ["jawa"] },
  { slug: "luke-skywalker", terms: ["luke skywalker", "farmboy luke", "luke"] },
  { slug: "darth-vader", terms: ["darth vader", "vader"] },
  { slug: "ben-obi-wan-kenobi", terms: ["ben obi-wan kenobi", "obi-wan", "obi wan", "ben kenobi", "ben"] },
  { slug: "princess-leia-organa", terms: ["princess leia", "leia organa", "leia"] },
  { slug: "han-solo", terms: ["han solo", "han"] },
  { slug: "chewbacca", terms: ["chewbacca", "chewie"] },
  { slug: "stormtrooper", terms: ["stormtrooper", "storm trooper"] },
  { slug: "r2-d2", terms: ["r2-d2", "r2d2", "r2"] },
  { slug: "c-3po", terms: ["c-3po", "c3po", "3po"] },
  { slug: "death-squad-commander", terms: ["death squad commander"] },
  { slug: "sand-people", terms: ["sand people", "sand person", "tusken"] }
];

function normalise(text) {
  return String(text || "")
    .toLowerCase()
    .replace(/[^a-z0-9\s\-]/g, " ")
    .replace(/\s+/g, " ")
    .trim();
}

function hasAny(text, terms) {
  return terms.some((term) => text.includes(term));
}

function fileExists(relPath) {
  return fs.existsSync(path.join(process.cwd(), relPath));
}

function readRel(relPath) {
  try {
    return fs.readFileSync(path.join(process.cwd(), relPath), "utf8");
  } catch {
    return "";
  }
}

function detectEntity(message) {
  const t = normalise(message);
  for (const item of FIGURE_ALIASES) {
    if (hasAny(t, item.terms)) return item.slug;
  }
  return null;
}

function detectAccessory(message) {
  const t = normalise(message);
  for (const [accessory, terms] of Object.entries(ACCESSORY_TERMS)) {
    if (hasAny(t, terms)) return accessory;
  }
  return null;
}

function detectIntent(message) {
  const t = normalise(message);
  if (detectAccessory(message)) return "accessory";
  if (
    t.includes("coo") ||
    t.includes("country of origin") ||
    t.includes("leg mark") ||
    t.includes("leg marking")
  ) return "figure";
  if (
    t.includes("id") ||
    t.includes("identify") ||
    t.includes("variant") ||
    t.includes("figure")
  ) return "figure";
  if (detectEntity(message)) return "figure";
  return "unknown";
}

function flowFilePath(flowId) {
  return path.join(FLOWS_ROOT, `${flowId}.json`);
}

function flowIdFor(entity, intent, accessory) {
  if (!entity) return null;

  if (intent === "figure") return `${entity}.figure`;

  if (intent === "accessory" && accessory) {
    const direct = `${entity}.${accessory}`;
    if (fs.existsSync(flowFilePath(direct))) return direct;

    if (entity === "jawa" && accessory === "cape") return "jawa.vinyl-cape";
    if (entity === "jawa" && accessory === "cloth-cloak") return "jawa.cloth-cloak";
    if (entity === "jawa" && accessory === "vinyl-cape") return "jawa.vinyl-cape";
    if (entity === "jawa" && accessory === "blaster") return "jawa.blaster";
  }

  return null;
}

function loadFlowById(flowId) {
  if (!flowId) return null;
  const file = flowFilePath(flowId);
  try {
    if (!fs.existsSync(file)) return null;
    return JSON.parse(fs.readFileSync(file, "utf8"));
  } catch (err) {
    console.error("Bad flow file", file, err);
    return null;
  }
}

function getStartStepId(flow) {
  return flow?.start_step || flow?.start || "start";
}

function getStep(flow, stepId) {
  return flow?.steps?.[stepId] || null;
}

function stepText(step) {
  return String(step?.content || step?.prompt || "").trim();
}

function normaliseOptions(step) {
  const options = step?.options;

  if (!options) return [];

  if (Array.isArray(options)) {
    return options;
  }

  if (typeof options === "object") {
    return Object.entries(options).map(([value, target]) => ({
      value,
      label: "",
      next: target
    }));
  }

  return [];
}

function optionMatch(input, step) {
  const t = normalise(input);
  const options = normaliseOptions(step);

  for (const option of options) {
    if (String(option.value).toLowerCase() === t) return option;

    if (option.label && normalise(option.label) === t) return option;

    if (Array.isArray(option.aliases)) {
      for (const alias of option.aliases) {
        const a = normalise(alias);
        if (a && (t === a || t.includes(a))) return option;
      }
    }
  }

  return null;
}

function imagesFromStep(step) {
  const images = [];

  if (!step) return images;

  if (Array.isArray(step.images)) {
    for (const img of step.images) {
      if (img && img.url) {
        images.push({
          title: img.title || "",
          url: img.url,
          caption: img.caption || ""
        });
      }
    }
  }

  if (step.type === "image" && step.url) {
    images.push({
      title: step.title || "",
      url: step.url,
      caption: step.caption || ""
    });
  }

  return images;
}

function questionReply(step) {
  let reply = stepText(step);
  const options = normaliseOptions(step);

  if (/reply with/i.test(reply)) {
    return reply.trim();
  }

  if (options.length) {
    const lines = options.map((option) => {
      const label = option.label || option.text || "";
      return label ? `${option.value} ${label}` : `${option.value}`;
    });

    reply = `${reply}\n\nReply with:\n\n${lines.join("\n")}`;
  }

  return reply.trim();
}

function routeTargetFromStep(step) {
  return step?.target || step?.flow || null;
}

function selectedTarget(option) {
  return option?.target || option?.flow || option?.next || null;
}

function makeResponse(reply, images, flowId, stepId, done = false) {
  return {
    reply: String(reply || "").trim(),
    images: images || [],
    flowState: done || !flowId || !stepId ? null : { flowId, stepId }
  };
}

function runFlowUntilQuestion(flowId, stepId, previousText = "", images = [], safety = 0) {
  if (safety > 20) return makeResponse(previousText || "Flow stopped.", images, null, null, true);

  const flow = loadFlowById(flowId);
  if (!flow) return null;

  const step = getStep(flow, stepId);
  if (!step) return null;

  images.push(...imagesFromStep(step));

  if (step.type === "route") {
    const target = routeTargetFromStep(step);
    const targetFlow = loadFlowById(target);
    if (!target || !targetFlow) {
      return makeResponse("I could not find that flow yet.", images, null, null, true);
    }
    return runFlowUntilQuestion(target, getStartStepId(targetFlow), previousText, images, safety + 1);
  }

  const text = stepText(step);
  const combinedText = [previousText, text].filter(Boolean).join("\n\n");

  if (step.type === "question" || normaliseOptions(step).length) {
    return makeResponse(questionReply(step), images, flowId, stepId);
  }

  if (step.type === "ai") {
    return makeResponse(
      combinedText || "Ask me your question and I’ll use the reference files to help.",
      images,
      null,
      null,
      true
    );
  }

  if (step.next) {
    return runFlowUntilQuestion(flowId, step.next, combinedText, images, safety + 1);
  }

  return makeResponse(combinedText, images, null, null, true);
}

function startFlow(flowId) {
  const flow = loadFlowById(flowId);
  if (!flow) return null;
  return runFlowUntilQuestion(flowId, getStartStepId(flow));
}

function continueFlow(flowState, message) {
  if (!flowState?.flowId || !flowState?.stepId) return null;

  const flow = loadFlowById(flowState.flowId);
  if (!flow) return null;

  const step = getStep(flow, flowState.stepId);
  if (!step) return null;

  const selected = optionMatch(message, step);

  if (!selected) {
    return makeResponse(
      `Please reply with one of the listed options.\n\n${questionReply(step)}`,
      [],
      flowState.flowId,
      flowState.stepId
    );
  }

  const target = selectedTarget(selected);

  if (!target) {
    return makeResponse(selected.reply || "Got it.", selected.images || [], null, null, true);
  }

  if (target.includes(".")) {
    return startFlow(target);
  }

  if (selected.reply) {
    return runFlowUntilQuestion(flowState.flowId, target, selected.reply, selected.images || []);
  }

  return runFlowUntilQuestion(flowState.flowId, target, "", selected.images || []);
}

function recentAssistantText(history, count = 6) {
  const items = Array.isArray(history) ? history : [];
  return items
    .filter((item) => item?.role === "assistant")
    .slice(-count)
    .map((item) => String(item.content || ""))
    .join("\n")
    .toLowerCase();
}

function isRecentJawaBlasterContext(history) {
  const text = recentAssistantText(history, 8);
  return (
    text.includes("jawa blaster") ||
    text.includes("jawa-blaster") ||
    text.includes("rear bump") ||
    text.includes("mould shape") ||
    text.includes("mold shape") ||
    text.includes("variantvillain.com/accessory-guide/jawa-blaster")
  );
}

function jawaBlasterFollowUp(message) {
  const t = normalise(message);

  if (t.includes("short")) {
    return makeResponse(
      `If the rear bump looks short, compare it against the M2 mould first.

M2 traits:
• shorter rear bump than M1
• cleaner, sharper mould detail
• scar to the top right of the bump

This is also the mould family used for the black Brazilian Glasslite version.

Compare the M2 examples here:
https://www.variantvillain.com/accessory-guide/jawa-blaster/#m2

If you are still unsure, the next useful check is whether the detail looks clean and sharp, or rougher/worn.`,
      [],
      null,
      null,
      true
    );
  }

  if (t.includes("long")) {
    return makeResponse(
      `If the rear bump looks long, compare it against the M1 Unitoy mould.

M1 traits:
• long rear bump
• visible gate scar near the handle
• slightly rougher finish
• distinctive bump at the bottom of the handle

Use the Jawa blaster guide here:
https://www.variantvillain.com/accessory-guide/jawa-blaster/`,
      [],
      null,
      null,
      true
    );
  }

  if (
    t.includes("no bump") ||
    t.includes("none") ||
    t.includes("missing bump") ||
    t.includes("without bump") ||
    t.includes("no rear bump")
  ) {
    return makeResponse(
      `If there is no rear bump, compare it against the M3 Kader mould.

M3 traits:
• no rear bump
• simplified shape compared with M1 and M2
• cleaner silhouette

Use the Jawa blaster guide here:
https://www.variantvillain.com/accessory-guide/jawa-blaster/`,
      [],
      null,
      null,
      true
    );
  }

  if (t.includes("rough") || t.includes("worn")) {
    return makeResponse(
      `A rougher or more worn finish can point more towards M1, but do not use texture alone.

Next compare the rear bump:
• long bump = M1
• short bump = M2
• no bump = M3

Jawa blaster guide:
https://www.variantvillain.com/accessory-guide/jawa-blaster/`,
      [],
      null,
      null,
      true
    );
  }

  if (t.includes("clean") || t.includes("sharp")) {
    return makeResponse(
      `Cleaner, sharper mould detail can point more towards M2 or M3.

Next check the rear bump:
• short bump = M2
• no bump = M3

M2 reference:
https://www.variantvillain.com/accessory-guide/jawa-blaster/#m2`,
      [],
      null,
      null,
      true
    );
  }

  if (t.includes("black")) {
    return makeResponse(
      `Black needs caution.

It could be:
• a reproduction
• a modern accessory
• a very dark blue original being mistaken for black
• or, less commonly, a Brazilian Glasslite black blaster

Place it against a strong light. If the edges look blue, it may actually be very dark blue / black-blue.

If it stays black, compare it especially against the M2 mould:
https://www.variantvillain.com/accessory-guide/jawa-blaster/#m2`,
      [],
      null,
      null,
      true
    );
  }

  if (t.includes("grey") || t.includes("gray")) {
    return makeResponse(
      `Grey needs extra caution.

Grey is a very common reproduction colour for Jawa blasters.

There are rare silver Glasslite versions, but they are extremely uncommon and should not be assumed.

Compare carefully here:
https://www.variantvillain.com/accessory-guide/jawa-blaster/`,
      [],
      null,
      null,
      true
    );
  }

  return makeResponse(
    `No problem. To narrow a Jawa blaster, the next best check is the rear bump.

Which does it look closest to?

1 Long rear bump = likely M1
2 Short rear bump = likely M2
3 No rear bump = likely M3

You can also compare here:
https://www.variantvillain.com/accessory-guide/jawa-blaster/`,
    [],
    null,
    null,
    true
  );
}

function walkFiles(dir) {
  const files = [];
  if (!fs.existsSync(dir)) return files;

  for (const item of fs.readdirSync(dir, { withFileTypes: true })) {
    const full = path.join(dir, item.name);
    if (item.isDirectory()) files.push(...walkFiles(full));
    else if (/\.(txt|json|md)$/i.test(item.name)) files.push(full);
  }

  return files;
}

function rel(filePath) {
  return path.relative(process.cwd(), filePath).replace(/\\/g, "/");
}

function sourceFilesFor(entity, intent, accessory) {
  const files = [];

  if (entity && intent === "figure") files.push(`data/figures/${entity}-reference.txt`);

  if (entity === "jawa" && accessory === "blaster") files.push("data/accessories/jawa-blaster.txt");
  if (entity === "jawa" && accessory === "cloth-cloak") files.push("data/accessories/jawa-cloak.txt");
  if (entity === "jawa" && accessory === "vinyl-cape") files.push("data/accessories/jawa-vinyl-cape.txt");
  if (entity === "jawa" && accessory === "cape") files.push("data/accessories/jawa-vinyl-cape.txt", "data/accessories/jawa-cloak.txt");
  if (entity === "stormtrooper" && accessory === "blaster") files.push("data/accessories/imperial-blaster.txt");
  if (entity === "princess-leia-organa" && accessory === "blaster") files.push("data/accessories/leia-blaster.txt");
  if (entity === "chewbacca" && accessory === "bowcaster") files.push("data/accessories/chewbacca-bowcaster.txt");

  if (accessory === "lightsaber") files.push("data/accessories/lightsaber.txt");

  const existing = files.filter(fileExists);
  if (existing.length) return existing.slice(0, 5);

  const all = walkFiles(DATA_ROOT);
  const terms = normalise(`${entity || ""} ${accessory || ""}`).split(" ").filter(Boolean);

  return all
    .map((file) => {
      const r = rel(file).toLowerCase();
      let score = 0;
      for (const term of terms) if (r.includes(term)) score += 10;
      if (intent === "figure" && r.includes("/figures/")) score += 4;
      if (intent === "accessory" && r.includes("/accessories/")) score += 4;
      return { file, score };
    })
    .filter((x) => x.score > 0)
    .sort((a, b) => b.score - a.score)
    .slice(0, 5)
    .map((x) => rel(x.file));
}

function sourceBlock(files) {
  return files
    .map((file) => `SOURCE FILE: ${file}\n${readRel(file).slice(0, 7000)}`)
    .join("\n\n---\n\n");
}

function buildSystemPrompt(files, message, entity, intent, accessory) {
  return `You are VF-CB, a Vintage Kenner Star Wars identification assistant.

Use the supplied local reference files as the source of truth.

Rules:
- Ask ONE question at a time.
- Prefer numbered replies.
- Keep answers concise.
- Do not repeat the same line twice.
- If a guided flow file exists, it should be used instead of inventing a new flow.
- If the user asks "id jawa" or "jawa figure", assume they mean the Jawa figure.
- If the user includes accessory words, treat it as an accessory request.
- If uncertain, ask a useful clarification question.
- Never claim something is original unless the evidence is strong.
- For valuable items, recommend confirmation from experienced collector groups.

Detected entity: ${entity || "unknown"}
Detected intent: ${intent || "unknown"}
Detected accessory: ${accessory || "none"}

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

  const cleanHistory = Array.isArray(history) ? history.slice(-10) : [];
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
  if (!response.ok) throw new Error(data?.error?.message || "Anthropic API error");

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
    const flowState = req.body?.flowState || null;

    if (!message) {
      res.status(400).json({ error: "Missing message" });
      return;
    }

    if (flowState?.flowId && flowState?.stepId) {
      const flowResponse = continueFlow(flowState, message);
      if (flowResponse) {
        res.status(200).json(flowResponse);
        return;
      }
    }

    const entity = detectEntity(message);
    const accessory = detectAccessory(message);
    const intent = detectIntent(message);
    const flowId = flowIdFor(entity, intent, accessory);

    if (flowId && fs.existsSync(flowFilePath(flowId))) {
      const flowResponse = startFlow(flowId);
      if (flowResponse) {
        res.status(200).json(flowResponse);
        return;
      }
    }

    if (!entity && !accessory && isRecentJawaBlasterContext(history)) {
      res.status(200).json(jawaBlasterFollowUp(message));
      return;
    }

    const files = sourceFilesFor(entity, intent, accessory);

    if (!files.length) {
      res.status(200).json({
        reply: `I’m not sure what you want to identify yet.

Tell me the figure or accessory, for example:

• Jawa figure
• Jawa blaster
• Luke lightsaber
• Stormtrooper blaster`,
        images: [],
        flowState: null
      });
      return;
    }

    const prompt = buildSystemPrompt(files, message, entity, intent, accessory);
    const text = await callClaude(prompt, history, message);
    const parsed = parseJson(text);

    if (!parsed || !parsed.reply) {
      res.status(200).json({
        reply: text || "I found the relevant file, but could not format a clean answer.",
        images: [],
        flowState: null
      });
      return;
    }

    res.status(200).json({
      reply: parsed.reply,
      images: Array.isArray(parsed.images) ? parsed.images : [],
      flowState: null
    });
  } catch (err) {
    console.error(err);
    res.status(500).json({ error: err.message || "Server error" });
  }
};
