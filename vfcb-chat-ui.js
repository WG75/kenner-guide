/* Follow-up helpers shared by the chat page and the tests. */

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
