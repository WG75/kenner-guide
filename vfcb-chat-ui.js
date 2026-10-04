/* Search and follow-up helpers shared by the chat page and the tests.
   Catalog parts have a name and era, not a per-item alias list, and they
   already sit near 7,000 characters. Search therefore matches the name,
   any aliases array an item happens to carry, text in parentheses, and a
   short nickname map. Typing in the box only returns results. It does not
   build a chat message. */

const NICKNAMES = {
  "chewbacca": ["chewie", "chewy"],
  "darth vader": ["vader"],
  "r2-d2": ["artoo", "r2d2"],
  "c-3po": ["threepio", "c3po"],
  "ben (obi-wan) kenobi": ["ben", "obi-wan", "kenobi"],
  "sand people": ["tusken", "tusken raider"],
  "jawa": ["jawas"]
};

const FOLLOW_SETS = {
  figure: [
    "Which cardbacks did it come on?",
    "What accessories came with it?",
    "How do I tell the variants apart?"
  ],
  accessory: [
    "Which figures came with it?",
    "What colours is it known in?",
    "How do I tell the moulds apart?"
  ],
  cardback: [
    "What else is documented on that card?",
    "Which factory is linked, if any?",
    "How do I tell the variants apart?"
  ],
  ranking: [
    "Which figure has the most variants?",
    "Which character has the most outfits?",
    "How many versions of Han Solo are there?"
  ],
  greeting: [
    "What does COO mean?",
    "What are the Last 17?",
    "Which figures are Early Bird?",
    "What is a debut cardback?"
  ],
  general: [
    "Which cardbacks did it come on?",
    "What accessories came with it?",
    "How do I tell the variants apart?"
  ]
};

const FOLLOW_START = "<<<FOLLOWUPS>>>";
const FOLLOW_END = "<<<END>>>";

function aliasStrings(item) {
  const out = [];
  if (Array.isArray(item.aliases)) out.push(...item.aliases);
  const name = String(item.name || "");
  for (const match of name.matchAll(/\(([^)]+)\)/g)) out.push(match[1]);
  const nick = NICKNAMES[name.toLowerCase()];
  if (nick) out.push(...nick);
  return out.map(value => String(value).trim()).filter(Boolean);
}

function searchScore(item, query, aliases) {
  const name = item.name.toLowerCase();
  let score = 0;
  if (name === query) score += 100;
  else if (name.startsWith(query)) score += 50;
  if (aliases.some(alias => alias.toLowerCase() === query)) score += 80;
  if (name.includes(query)) score += 20;
  return score;
}

/* Case-insensitive. Every query word must appear in the name or an alias,
   either as a substring or as the start of a word. */
export function searchCatalog(items, query, limit = 8) {
  const q = String(query || "").trim().toLowerCase();
  if (!q) return [];
  const words = q.split(/\s+/).filter(Boolean);
  const scored = [];
  for (const item of items || []) {
    if (!item || !item.name) continue;
    const aliases = aliasStrings(item);
    const hay = [item.name, ...aliases].join(" ").toLowerCase();
    const tokens = hay.split(/[^a-z0-9]+/).filter(Boolean);
    const matched = words.every(word => hay.includes(word) || tokens.some(token => token.startsWith(word)));
    if (!matched) continue;
    scored.push({
      name: item.name,
      type: item.type === "accessory" ? "accessory" : "figure",
      era: item.era || "",
      file: item.file || "",
      score: searchScore(item, q, aliases)
    });
  }
  scored.sort((a, b) => b.score - a.score || a.name.localeCompare(b.name));
  return scored.slice(0, limit);
}

/* The characters in the search box are not a chat message. */
export function previewSearch(query, items) {
  return { results: searchCatalog(items, query), chatMessage: null };
}

/* A chosen result opens chat with a natural question, not the typed text. */
export function openSearchResult(item) {
  const name = String(item && item.name || "").trim();
  return {
    chatMessage: name ? `Tell me about ${name}` : "",
    typedQuerySent: false
  };
}

function cleanFollowUpLines(list) {
  const seen = new Set();
  const out = [];
  for (const entry of list) {
    const label = String(entry || "").replace(/^[-*\d.)\s]+/, "").trim();
    if (!label || label.includes("<<<") || label.length > 120) continue;
    const key = label.toLowerCase();
    if (seen.has(key)) continue;
    seen.add(key);
    out.push(label);
    if (out.length === 3) break;
  }
  return out.length >= 2 ? out : [];
}

function stripFollowDelimiters(text) {
  return String(text || "")
    .replaceAll(FOLLOW_START, "")
    .replaceAll(FOLLOW_END, "")
    .trim();
}

/* Pull follow-ups out of a model reply. Missing or broken blocks return
   followUps: null so the caller can use a fallback. Delimiters never remain
   in the reply text. */
export function parseFollowUps(text) {
  const raw = String(text || "");
  const trimmed = raw.trim();
  if (trimmed.startsWith("{") && trimmed.endsWith("}")) {
    try {
      const obj = JSON.parse(trimmed);
      if (obj && typeof obj.reply === "string" && Array.isArray(obj.followUps)) {
        const followUps = cleanFollowUpLines(obj.followUps);
        if (followUps.length >= 2) {
          return { reply: stripFollowDelimiters(obj.reply), followUps };
        }
      }
    } catch (err) {
      /* not JSON; try the delimited block */
    }
  }
  const start = raw.lastIndexOf(FOLLOW_START);
  const end = raw.lastIndexOf(FOLLOW_END);
  if (start !== -1 && end > start) {
    const body = raw.slice(start + FOLLOW_START.length, end);
    const followUps = cleanFollowUpLines(body.split(/\n+/));
    const reply = stripFollowDelimiters(raw.slice(0, start));
    if (followUps.length >= 2) return { reply, followUps };
    return { reply, followUps: null };
  }
  return { reply: stripFollowDelimiters(raw), followUps: null };
}

export function followTopicFor(text) {
  const lower = String(text || "").toLowerCase();
  if (/^(?:hi|hello|hey|thanks|thank you|thank)\b/.test(lower.trim())) return "greeting";
  if (/\b(?:most|fewest|how many|number of)\b/.test(lower) && /\b(?:variants?|outfits?|versions?|looks?|characters?)\b/.test(lower)) return "ranking";
  if (/\b(?:card ?backs?|which cards?|what cards?)\b/.test(lower)) return "cardback";
  if (/\b(?:accessor(?:y|ies)|moulds?|molds?|blaster|cape|cloak|rifle|bowcaster|lightsaber)\b/.test(lower)) return "accessory";
  return "figure";
}

/* Empty chat is a compact welcome block. The first user message switches
   the page to a scrolling transcript with the composer docked at the bottom. */
export function layoutMode(userMessageCount) {
  return Number(userMessageCount) > 0 ? "chatting" : "welcome";
}

export function syncLayoutClass(classList, userMessageCount) {
  const mode = layoutMode(userMessageCount);
  classList.toggle("welcome", mode === "welcome");
  classList.toggle("chatting", mode === "chatting");
  return mode;
}

export function fallbackFollowUps(topic) {
  const set = FOLLOW_SETS[topic] || FOLLOW_SETS.general;
  if (topic === "greeting") return set.slice();
  return set.slice(0, 3);
}
