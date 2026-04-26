const fs = require("fs");
const path = require("path");

const DATA_ROOT = path.join(process.cwd(), "data");
const FLOWS_ROOT = path.join(DATA_ROOT, "flows");
const MODEL = process.env.ANTHROPIC_MODEL || "claude-haiku-4-5-20251001";

const ACCESSORY_TERMS = {
  blaster: ["blaster","gun","pistol","weapon","laser","laser gun","laser pistol","ray","ray gun","shooter","zapper","pew","pew pew","sidearm"],
  lightsaber: ["lightsaber","light saber","saber","sabre"],
  cape: ["cape","vinyl cape"],
  cloak: ["cloak","cloth cloak","robe"],
  bowcaster: ["bowcaster","bow caster"],
  gaderffi: ["gaffi","gaffi stick","gaderffii","gaderffi"]
};

const FIGURE_ALIASES = [
  { slug: "jawa", terms: ["jawa"] },
  { slug: "luke-skywalker", terms: ["luke skywalker","farmboy luke","luke"] },
  { slug: "darth-vader", terms: ["darth vader","vader"] },
  { slug: "ben-obi-wan-kenobi", terms: ["ben obi-wan kenobi","obi-wan","obi wan","ben kenobi","ben"] },
  { slug: "princess-leia-organa", terms: ["princess leia","leia organa","leia"] },
  { slug: "han-solo", terms: ["han solo","han"] },
  { slug: "chewbacca", terms: ["chewbacca","chewie"] },
  { slug: "stormtrooper", terms: ["stormtrooper","storm trooper"] },
  { slug: "r2-d2", terms: ["r2-d2","r2d2","r2"] },
  { slug: "c-3po", terms: ["c-3po","c3po","3po"] },
  { slug: "death-squad-commander", terms: ["death squad commander"] },
  { slug: "sand-people", terms: ["sand people","sand person","tusken"] }
];

function normalise(text) {
  return String(text || "").toLowerCase().replace(/[^a-z0-9\s\-]/g, " ").replace(/\s+/g, " ").trim();
}

function hasAny(text, terms) {
  return terms.some((term) => text.includes(term));
}

function fileExists(relPath) {
  return fs.existsSync(path.join(process.cwd(), relPath));
}

function readRel(relPath) {
  try { return fs.readFileSync(path.join(process.cwd(), relPath), "utf8"); } catch { return ""; }
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
  if (t.includes("coo") || t.includes("country of origin") || t.includes("leg mark") || t.includes("leg marking")) return "figure";
  if (t.includes("id") || t.includes("identify") || t.includes("variant") || t.includes("figure")) return "figure";
  if (detectEntity(message)) return "figure";
  return "unknown";
}

function flowPath(entity, intent, accessory) {
  if (!entity) return null;
  if (intent === "figure") {
    const candidate = path.join(FLOWS_ROOT, `${entity}.figure.json`);
    if (fs.existsSync(candidate)) return candidate;
  }
  if (intent === "accessory" && accessory) {
    const candidate = path.join(FLOWS_ROOT, `${entity}.${accessory}.json`);
    if (fs.existsSync(candidate)) return candidate;
  }
  return null;
}

function loadFlow(filePath) {
  try { return JSON.parse(fs.readFileSync(filePath, "utf8")); } catch (err) { console.error("Bad flow file", filePath, err); return null; }
}

function lastAssistant(history) {
  const items = Array.isArray(history) ? history : [];
  for (let i = items.length - 1; i >= 0; i--) {
    if (items[i]?.role === "assistant") return String(items[i].content || "");
  }
  return "";
}

function inferFlowState(history) {
  const assistant = lastAssistant(history);
  const match = assistant.match(/\[vfcb-state:([^\]]+)\]/);
  return match ? match[1].trim() : null;
}

function stripStateMarker(text) {
  return String(text || "").replace(/\n?\[vfcb-state:[^\]]+\]/g, "").trim();
}

function optionMatch(input, options) {
  const t = normalise(input);
  for (const option of options || []) {
    if (String(option.value).toLowerCase() === t) return option;
    if (normalise(option.label || "") === t) return option;
    if (Array.isArray(option.aliases) && option.aliases.some((a) => normalise(a) === t || t.includes(normalise(a)))) return option;
  }
  return null;
}

function stateWithMarker(text, nextState) {
  if (!nextState) return text;
  return `${text}\n\n[vfcb-state:${nextState}]`;
}

function formatFlowStep(step) {
  let reply = step.prompt || "";
  if (Array.isArray(step.options) && step.options.length) {
    const optionLines = step.options.map((option) => `${option.value} ${option.label}`).join("\n");
    reply = `${reply}\n\nReply with:\n\n${optionLines}`;
  }
  return reply.trim();
}

function getStep(flow, stepId) {
  return flow?.steps?.[stepId] || null;
}

function flowStartResponse(flow) {
  const startId = flow?.start;
  const step = getStep(flow, startId);
  if (!step) return null;
  return { reply: stateWithMarker(formatFlowStep(step), startId), images: step.images || [] };
}

function startNamedFlow(flowId) {
  const file = path.join(FLOWS_ROOT, `${flowId}.json`);
  if (!fs.existsSync(file)) return null;
  const flow = loadFlow(file);
  return flowStartResponse(flow);
}

function flowNextResponse(flow, currentState, message) {
  const step = getStep(flow, currentState);
  if (!step) return null;
  const selected = optionMatch(message, step.options || []);
  if (!selected) {
    return { reply: stateWithMarker(`Please reply with one of the listed options.\n\n${formatFlowStep(step)}`, currentState), images: [] };
  }
  if (selected.flow) return startNamedFlow(selected.flow);
  if (selected.reply) {
    if (selected.next) {
      const nextStep = getStep(flow, selected.next);
      if (!nextStep) return { reply: stripStateMarker(selected.reply), images: selected.images || [] };
      return { reply: stateWithMarker(`${selected.reply}\n\n${formatFlowStep(nextStep)}`.trim(), selected.next), images: nextStep.images || [] };
    }
    return { reply: stripStateMarker(selected.reply), images: selected.images || [] };
  }
  if (selected.next) {
    const nextStep = getStep(flow, selected.next);
    if (!nextStep) return null;
    return { reply: stateWithMarker(formatFlowStep(nextStep), selected.next), images: nextStep.images || [] };
  }
  return null;
}

function findActiveFlow(history) {
  const state = inferFlowState(history);
  if (!state) return null;
  const allFlowFiles = walkFiles(FLOWS_ROOT).filter((f) => f.endsWith(".json"));
  for (const file of allFlowFiles) {
    const flow = loadFlow(file);
    if (flow?.steps?.[state]) return { flow, state, file };
  }
  return null;
}

function sourceFilesFor(entity, intent, accessory) {
  const files = [];
  if (entity && intent === "figure") files.push(`data/figures/${entity}-reference.txt`);
  if (entity === "jawa" && accessory === "blaster") files.push("data/accessories/jawa-blaster.txt");
  if (entity === "jawa" && accessory === "cloak") files.push("data/accessories/jawa-cloak.txt");
  if (entity === "jawa" && accessory === "cape") files.push("data/accessories/jawa-vinyl-cape.txt", "data/accessories/jawa-cloak.txt");
  if (entity === "stormtrooper" && accessory === "blaster") files.push("data/accessories/imperial-blaster.txt");
  if (entity === "leia" && accessory === "blaster") files.push("data/accessories/leia-blaster.txt");
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
  return files.map((file) => `SOURCE FILE: ${file}\n${readRel(file).slice(0, 7000)}`).join("\n\n---\n\n");
}

function buildSystemPrompt(files, message, entity, intent, accessory) {
  return `You are VF-CB, a Vintage Kenner Star Wars identification assistant.

Use the supplied local reference files as the source of truth.

Rules:
- Ask ONE question at a time.
- Prefer numbered replies.
- Keep answers concise.
- Do not repeat the same line twice.
- Do not invent a guided flow if a flow file should exist.
- If the user asks "id jawa", assume they mean the Jawa figure.
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
    messages.push({ role: item.role, content: stripStateMarker(String(item.content)).slice(0, 1500) });
  }
  messages.push({ role: "user", content: message });
  const response = await fetch("https://api.anthropic.com/v1/messages", {
    method: "POST",
    headers: { "Content-Type": "application/json", "x-api-key": apiKey, "anthropic-version": "2023-06-01" },
    body: JSON.stringify({ model: MODEL, max_tokens: 700, temperature: 0.1, system: systemPrompt, messages })
  });
  const data = await response.json();
  if (!response.ok) throw new Error(data?.error?.message || "Anthropic API error");
  return data?.content?.[0]?.text || "";
}

function parseJson(text) {
  try { return JSON.parse(text); } catch {
    const start = text.indexOf("{");
    const end = text.lastIndexOf("}");
    if (start >= 0 && end > start) {
      try { return JSON.parse(text.slice(start, end + 1)); } catch { return null; }
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

    const active = findActiveFlow(history);
    if (active) {
      const flowResponse = flowNextResponse(active.flow, active.state, message);
      if (flowResponse) {
        flowResponse.reply = stripStateMarker(flowResponse.reply);
        res.status(200).json(flowResponse);
        return;
      }
    }

    const entity = detectEntity(message);
    const accessory = detectAccessory(message);
    const intent = detectIntent(message);
    const maybeFlow = flowPath(entity, intent, accessory);

    if (maybeFlow) {
      const flow = loadFlow(maybeFlow);
      const response = flowStartResponse(flow);
      if (response) {
        res.status(200).json(response);
        return;
      }
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
        images: []
      });
      return;
    }

    const prompt = buildSystemPrompt(files, message, entity, intent, accessory);
    const text = await callClaude(prompt, history, message);
    const parsed = parseJson(text);

    if (!parsed || !parsed.reply) {
      res.status(200).json({ reply: stripStateMarker(text) || "I found the relevant file, but could not format a clean answer.", images: [] });
      return;
    }

    res.status(200).json({ reply: stripStateMarker(parsed.reply), images: Array.isArray(parsed.images) ? parsed.images : [] });
  } catch (err) {
    console.error(err);
    res.status(500).json({ error: err.message || "Server error" });
  }
};