import fs from "fs";
import path from "path";

const FILE = path.join(process.cwd(), "data", "coo-figures.json");
const VV_MANIFEST = path.join(process.cwd(), "images", "variant-villain", "manifest.json");

export const COO_EXPLANATION = "The country of origin (COO) stamp is the small text on the back of the legs saying where it was made. A partial or cut-off country name counts as No COO.";

function cooExplanation(record) {
  const custom = record && String(record.cooExplanation || "").trim();
  return custom ? withoutMexico(custom) : COO_EXPLANATION;
}

function vvManifest() {
  try {
    return JSON.parse(fs.readFileSync(VV_MANIFEST, "utf8"));
  } catch {
    return null;
  }
}

function stampImage(record) {
  const image = record && record.referenceImage;
  const id = image && String(image.id || "").trim();
  if (!id) return null;
  const manifest = vvManifest();
  if (!manifest || manifest.show !== true) return null;
  const entries = Array.isArray(manifest.images) ? manifest.images : [];
  const entry = entries.find(item => item && String(item.id || "") === id);
  if (!entry || !entry.file) return null;
  const credit = String(entry.credit || "");
  return {
    url: `/images/variant-villain/${entry.file}`,
    alt: String(entry.alt || ""),
    title: String(entry.title || ""),
    caption: credit,
    credit,
    sourcePage: ""
  };
}

function withStampImage(result, record) {
  const image = stampImage(record);
  if (image) result.images = [image];
  return result;
}

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

function done(reply, match) {
  const result = {
    reply,
    actions: [],
    quickReplies: false,
    flowState: null
  };
  if (match) result.match = match;
  return result;
}

function figureMatch(record, factory) {
  const name = String(factory || "").trim();
  if (!record || !name) return null;
  return { figure: record.name, factory: name, sourceUrl: record.sourceUrl || "" };
}

export function cooOpening(displayName) {
  const name = String(displayName || "").trim();
  const record = cooRecordFor(name);
  const options = record && Array.isArray(record.options) ? record.options.map(speakable).filter(Boolean) : [];
  const factory = record && String(record.singleFactory || "").trim();
  const verified = record && record.verified && (options.length > 0 || factory);
  if (!verified) {
    return done(`Let's check ${name}. I don't have verified COO details for that figure, so I won't guess a country list.`);
  }
  record.options = options;
  record.whereToLook = withoutMexico(record.whereToLook);
  const where = record.whereToLook;
  const ask = withoutMexico(record.ask || "Which stamp do you see?");
  const lines = [
    cooExplanation(record),
    "The country stamp is the first check. When more than one factory used that stamp, the stamp alone is not the variant.",
    "",
    `Let's check ${name}. ${where}`.trim()
  ];
  if (factory) {
    lines.push("", `This figure was made only by ${factory}. There is no factory choice to make.`);
  }
  if (!options.length) {
    return done(lines.join("\n"), figureMatch(record, factory));
  }
  lines.push("", ask);
  return withStampImage({
    reply: lines.join("\n"),
    actions: record.options.map(choice),
    quickReplies: true,
    flowState: {
      topic: "variant_identify",
      displayName: record.name,
      step: "coo",
      optionId: "",
      answers: [],
      photoTells: [],
      usedTells: []
    }
  }, record);
}

const TELL_ORDER = ["hair", "paint", "plastic", "head", "mould", "date", "cavity", "assembly", "accessory", "cardback"];

function listNames(items) {
  const labelled = items.map(item => `the ${item}`);
  if (labelled.length <= 1) return labelled[0] || "";
  if (labelled.length === 2) return `${labelled[0]} and ${labelled[1]}`;
  return `${labelled.slice(0, -1).join(", ")}, and ${labelled[labelled.length - 1]}`;
}

function candidateMatches(candidate, factory) {
  const cand = norm(candidate);
  const fac = norm(factory);
  if (!fac || !(cand === fac || cand.startsWith(`${fac} `))) return false;
  if (cand.includes("china") && !fac.includes("china")) return false;
  if (cand.includes("ledy") && !fac.includes("ledy")) return false;
  if (cand.includes("toys") && !fac.includes("toys")) return false;
  return true;
}

function tellHits(tell, candidates) {
  return candidates.filter(candidate => (tell.factories || []).some(factory => candidateMatches(candidate, factory)));
}

function pickTell(record, candidates, used) {
  let best = null;
  for (const category of TELL_ORDER) {
    if (used.includes(category)) continue;
    const tells = (record.tells || []).filter(tell => tell.category === category && tellHits(tell, candidates).length);
    const signatures = new Set(tells.map(tell => tellHits(tell, candidates).join("|")).filter(Boolean));
    if (signatures.size < 2) continue;
    const covered = new Set(tells.flatMap(tell => tellHits(tell, candidates)));
    const score = signatures.size * 10 + covered.size + (TELL_ORDER.length - TELL_ORDER.indexOf(category));
    if (!best || score > best.score) best = { category, tells, score };
  }
  return best;
}

function photoHit(tell, photoTells) {
  const blobWords = new Set(norm((photoTells || []).join(" ")).split(" ").filter(Boolean));
  if (!blobWords.size) return false;
  const skip = new Set(["with", "from", "that", "this", "figure", "early", "later", "smile", "kader", "unitoy", "taiwan", "poch", "glasslite"]);
  const words = norm(tell.detail).split(" ").filter(word => word.length > 4 && !skip.has(word));
  const hits = new Set(words.filter(word => blobWords.has(word)));
  return hits.size >= 2 || [...hits].some(word => word.length > 5);
}

function settleLine(record, candidates, used) {
  const left = TELL_ORDER.filter(category => !used.includes(category) && (record.tells || []).some(tell => tell.category === category && tellHits(tell, candidates).length));
  if (left.length) return `The reference data still has ${left.join(", ")} notes that were not enough to separate them.`;
  return "Nothing else in the reference data separates them. A mould detail, paint colour, plastic colour, or the accessory with it would settle it.";
}

function remain(record, candidates, used) {
  return done(
    `I'm not sure which of those it is. ${listNames(candidates)} still match. ${settleLine(record, candidates, used)}`
  );
}

function finishShared(record, candidates, used, conclusion) {
  const extra = settleLine(record, candidates, used);
  const base = String(conclusion || "").trim();
  if (!base) return remain(record, candidates, used);
  return done(base.includes(extra) ? base : `${base} ${extra}`);
}

function concludeOne(record, factory, because) {
  return done(`That is the ${factory}. ${because}`.trim(), figureMatch(record, factory));
}

function askTell(record, candidates, flowState, answers, conclusion) {
  const used = Array.isArray(flowState.usedTells) ? flowState.usedTells : [];
  const photoTells = Array.isArray(flowState.photoTells) ? flowState.photoTells : [];
  const picked = pickTell(record, candidates, used);
  if (!picked) {
    if (!used.length && conclusion) return finishShared(record, candidates, used, conclusion);
    return remain(record, candidates, used);
  }
  const seen = photoTells.length
    ? picked.tells.filter(tell => photoHit(tell, photoTells))
    : [];
  const seenSets = new Set(seen.map(tell => tellHits(tell, candidates).join("|")).filter(Boolean));
  if (seen.length && seenSets.size === 1) {
    const next = tellHits(seen[0], candidates);
    const note = `The photo shows a match for “${seen[0].detail}”.`;
    if (next.length === 1) return concludeOne(record, next[0], `${note} The country stamp was shared, and that tell matches this mould.`);
    if (next.length > 1 && next.length < candidates.length) {
      return askTell(record, next, { ...flowState, usedTells: [...used, picked.category], photoTells: [] }, answers.concat(note));
    }
  }
  const buttons = [];
  for (const tell of picked.tells) {
    const label = tell.detail.length > 110 ? `${tell.detail.slice(0, 107).trim()}...` : tell.detail;
    if (!buttons.some(item => norm(item.label) === norm(label))) buttons.push({ label, tell });
    if (buttons.length === 6) break;
  }
  buttons.push({ label: "I'm not sure", tell: null });
  return {
    reply: [
      `That stamp is shared by ${listNames(candidates)}. The country stamp alone cannot separate them.`,
      "",
      picked.tells[0].where || "Look at the next detail.",
      "",
      "Which of these do you see?"
    ].join("\n"),
    actions: buttons.map(item => ({ label: item.label, value: item.label })),
    quickReplies: true,
    flowState: {
      topic: "variant_identify",
      displayName: record.name,
      step: "tell",
      optionId: candidates.join("|"),
      answers,
      photoTells,
      usedTells: [...used, picked.category]
    }
  };
}

function afterStamp(record, factories, conclusion, sure, flowState, answers) {
  const names = (factories || []).filter(Boolean);
  if (sure || names.length <= 1) return done(conclusion, names.length === 1 ? figureMatch(record, names[0]) : null);
  return askTell(record, names, flowState, answers, conclusion);
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
  const carried = {
    photoTells: Array.isArray(flowState.photoTells) ? flowState.photoTells : [],
    usedTells: Array.isArray(flowState.usedTells) ? flowState.usedTells : []
  };
  if (flowState.step === "tell") {
    const candidates = String(flowState.optionId || "").split("|").filter(Boolean);
    if (norm(text) === "i m not sure" || norm(text) === "im not sure") {
      return remain(record, candidates, carried.usedTells);
    }
    const used = carried.usedTells;
    const category = used[used.length - 1];
    const tells = (record.tells || []).filter(tell => tell.category === category);
    const tell = tells.find(item => norm(item.detail) === norm(text) || norm(item.detail).startsWith(norm(text.replace(/\.\.\.$/, ""))));
    if (!tell) return done(`I'm not sure. That isn't one of the verified tells for ${record.name}.`);
    const next = tellHits(tell, candidates);
    if (next.length === 1) {
      return concludeOne(record, next[0], `The country stamp was shared, and “${tell.detail}” matches this mould.`);
    }
    if (!next.length) return remain(record, candidates, used);
    return askTell(record, next, { ...flowState, photoTells: [] }, answers);
  }
  if (flowState.step === "follow") {
    const parent = (record.options || []).find(option => option.id === flowState.optionId);
    const follow = parent ? findFollowUp(parent, text) : null;
    if (!follow) {
      return done(`I'm not sure. That isn't one of the verified stamps for ${record.name}.`);
    }
    if (Array.isArray(follow.factories) && follow.factories.length) {
      return afterStamp(record, follow.factories, follow.conclusion, follow.sure, { ...flowState, ...carried }, answers);
    }
    return done(follow.conclusion || `I'm not sure which factory that is for ${record.name}.`);
  }
  const option = findOption(record, text);
  if (!option) {
    return done(`I'm not sure. That isn't one of the verified stamps for ${record.name}.`);
  }
  if (Array.isArray(option.followUps) && option.followUps.length) {
    return withStampImage({
      reply: `One more look at ${record.name}. ${record.whereToLook}\n\nWhich of these is it?`,
      actions: option.followUps.map(choice),
      quickReplies: true,
      flowState: {
        topic: "variant_identify",
        displayName: record.name,
        step: "follow",
        optionId: option.id,
        answers,
        photoTells: carried.photoTells,
        usedTells: carried.usedTells
      }
    }, record);
  }
  return afterStamp(
    record,
    option.factories,
    option.conclusion || `I'm not sure which factory that is for ${record.name}.`,
    option.sure,
    { ...flowState, ...carried },
    answers
  );
}
