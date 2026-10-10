import fs from "fs";
import path from "path";

const FILE = path.join(process.cwd(), "data", "coo-figures.json");

export const COO_EXPLANATION = "The country of origin (COO) stamp is the small text on the back of the legs saying where it was made. A partial or cut-off country name counts as No COO.";

let cache = null;

function load() {
  if (cache) return cache;
  const parsed = JSON.parse(fs.readFileSync(FILE, "utf8"));
  cache = Array.isArray(parsed.figures) ? parsed.figures : [];
  return cache;
}

function norm(value) {
  return String(value || "").toLowerCase().replace(/[^a-z0-9]+/g, " ").trim();
}

function tokens(value) {
  return norm(value).split(" ").filter(tok => tok && tok !== "the" && tok !== "with" && tok !== "in");
}

export function cooRecordFor(displayName) {
  const want = norm(displayName);
  if (!want) return null;
  const figures = load();
  const exact = figures.find(fig => norm(fig.name) === want);
  if (exact) return exact;
  const wantTokens = new Set(tokens(displayName));
  const contained = figures.filter(fig => {
    const nameTokens = tokens(fig.name);
    return nameTokens.length > 0 && nameTokens.every(tok => wantTokens.has(tok));
  });
  if (!contained.length) return null;
  contained.sort((a, b) => tokens(b.name).length - tokens(a.name).length);
  const best = tokens(contained[0].name).length;
  const top = contained.filter(fig => tokens(fig.name).length === best);
  return top.length === 1 ? top[0] : null;
}

function withoutMexico(text) {
  return String(text || "").replace(/\bMexico\b/gi, "").replace(/[ ]{2,}/g, " ").replace(/\s+([,.])/g, "$1").trim();
}

function speakable(option) {
  if (!option || /mexico/i.test(option.label || "")) return null;
  const followUps = (option.followUps || []).map(speakable).filter(Boolean);
  return {
    ...option,
    label: withoutMexico(option.label),
    conclusion: withoutMexico(option.conclusion),
    whereToLook: withoutMexico(option.whereToLook),
    followUps
  };
}

function choice(option) {
  return { label: option.label, value: option.label };
}

function done(reply) {
  return {
    reply,
    actions: [],
    quickReplies: false,
    flowState: null
  };
}

export function cooOpening(displayName) {
  const name = String(displayName || "").trim();
  const record = cooRecordFor(name);
  const options = record && Array.isArray(record.options) ? record.options.map(speakable).filter(Boolean) : [];
  const verified = record && record.verified && options.length > 0;
  if (!verified) {
    return done(`Let's check ${name}. I don't have verified COO details for that figure, so I won't guess a country list.`);
  }
  record.options = options;
  record.whereToLook = withoutMexico(record.whereToLook);
  const where = record.whereToLook;
  const reply = [
    COO_EXPLANATION,
    "",
    `Let's check ${name}. ${where}`.trim(),
    "",
    "Which stamp do you see?"
  ].join("\n");
  return {
    reply,
    actions: record.options.map(choice),
    quickReplies: true,
    flowState: {
      topic: "variant_identify",
      displayName: record.name,
      step: "coo",
      optionId: "",
      answers: []
    }
  };
}

function findOption(record, message) {
  const want = norm(message);
  return (record.options || []).find(option => norm(option.label) === want || norm(option.id) === want) || null;
}

function findFollowUp(option, message) {
  const want = norm(message);
  return (option.followUps || []).find(item => norm(item.label) === want || norm(item.id) === want) || null;
}

export function cooContinue(flowState, message) {
  const record = cooRecordFor(flowState && flowState.displayName);
  if (!record || !record.verified) {
    return done("I don't have verified COO details for that figure, so I won't guess a country list.");
  }
  const text = String(message || "").trim();
  const answers = Array.isArray(flowState.answers) ? [...flowState.answers, text] : [text];
  if (flowState.step === "follow") {
    const parent = (record.options || []).find(option => option.id === flowState.optionId);
    const follow = parent ? findFollowUp(parent, text) : null;
    if (!follow) {
      return done(`I'm not sure. That isn't one of the verified stamps for ${record.name}.`);
    }
    return done(follow.conclusion || `I'm not sure which factory that is for ${record.name}.`);
  }
  const option = findOption(record, text);
  if (!option) {
    return done(`I'm not sure. That isn't one of the verified stamps for ${record.name}.`);
  }
  if (Array.isArray(option.followUps) && option.followUps.length) {
    return {
      reply: `One more look at ${record.name}. ${record.whereToLook}\n\nWhich of these is it?`,
      actions: option.followUps.map(choice),
      quickReplies: true,
      flowState: {
        topic: "variant_identify",
        displayName: record.name,
        step: "follow",
        optionId: option.id,
        answers
      }
    };
  }
  return done(option.conclusion || `I'm not sure which factory that is for ${record.name}.`);
}
