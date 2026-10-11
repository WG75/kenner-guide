import fs from "fs";
import path from "path";

const FILE = path.join(process.cwd(), "data", "factory-match.json");
const TELL_ORDER = ["plastic", "pin", "letter", "gloss", "mould", "paint", "hair", "head", "date", "cavity", "assembly", "cardback", "accessory"];

let cache = null;

function load() {
  if (cache) return cache;
  cache = JSON.parse(fs.readFileSync(FILE, "utf8"));
  return cache;
}

function norm(value) {
  return String(value || "").toLowerCase().replace(/[^a-z0-9]+/g, " ").trim();
}

function factoryMatches(candidate, factory) {
  const cand = norm(candidate);
  const fac = norm(factory);
  if (!fac || !(cand === fac || cand.startsWith(`${fac} `))) return false;
  if (cand.includes("china") && !fac.includes("china")) return false;
  if (cand.includes("ledy") && !fac.includes("ledy")) return false;
  if (cand.includes("toys") && !fac.includes("toys")) return false;
  return true;
}

function listNames(items) {
  const labelled = items.map(item => item.label || `${item.factory} ${item.mould}`.trim());
  if (labelled.length <= 1) return labelled[0] || "";
  if (labelled.length === 2) return `${labelled[0]} and ${labelled[1]}`;
  return `${labelled.slice(0, -1).join(", ")}, and ${labelled[labelled.length - 1]}`;
}

function variantLabel(variant) {
  return `${variant.factory} ${variant.mould} ${variant.accessory}`.replace(/\s+/g, " ").trim();
}

function figureVariantsFor(match) {
  const data = load();
  return (data.figureVariants || []).filter(variant =>
    norm(variant.figure) === norm(match.figure) && factoryMatches(variant.factory, match.factory)
  );
}

function accessoriesForFigure(figureName) {
  const data = load();
  const ids = new Set((data.figureVariants || []).filter(variant => norm(variant.figure) === norm(figureName)).map(variant => variant.id));
  const names = new Set();
  for (const variant of data.accessoryVariants || []) {
    if ((variant.cardedWith || []).some(id => ids.has(id))) names.add(variant.accessory);
  }
  return [...names];
}

function variantsOf(accessory) {
  const want = norm(accessory);
  return (load().accessoryVariants || []).filter(variant => norm(variant.accessory) === want);
}

function findAccessory(name) {
  const want = norm(name);
  if (!want) return "";
  const names = [...new Set((load().accessoryVariants || []).map(variant => variant.accessory))];
  const exact = names.find(item => norm(item) === want);
  if (exact) return exact;
  const contained = names.filter(item => norm(item).includes(want) || want.includes(norm(item)));
  contained.sort((a, b) => norm(a).length - norm(b).length);
  return contained.length === 1 ? contained[0] : "";
}

function tellHits(tell, variants) {
  const detail = norm(tell.detail);
  return variants.filter(variant => (variant.tells || []).some(item => norm(item.detail) === detail));
}

function pickTell(variants, used) {
  let best = null;
  const pool = [];
  for (const variant of variants) {
    for (const tell of variant.tells || []) pool.push({ ...tell, variant });
  }
  for (const category of TELL_ORDER) {
    if (used.includes(category)) continue;
    const tells = [];
    const seen = new Set();
    for (const item of pool) {
      if (item.category !== category) continue;
      const key = norm(item.detail);
      if (seen.has(key)) continue;
      seen.add(key);
      const hits = variants.filter(variant => (variant.tells || []).some(tell => norm(tell.detail) === key));
      if (hits.length) tells.push({ ...item, hits });
    }
    const signatures = new Set(tells.map(tell => tell.hits.map(variant => variant.id).sort().join("|")));
    if (signatures.size < 2) continue;
    const covered = new Set(tells.flatMap(tell => tell.hits.map(variant => variant.id)));
    const score = signatures.size * 10 + covered.size + (TELL_ORDER.length - TELL_ORDER.indexOf(category));
    if (!best || score > best.score) best = { category, tells, score };
  }
  return best;
}

function photoHit(detail, photoTells) {
  const blob = new Set(norm((photoTells || []).join(" ")).split(" ").filter(Boolean));
  if (!blob.size) return false;
  const skip = new Set(["with", "from", "that", "this", "smile", "kader", "unitoy", "staff", "blaster"]);
  const words = norm(detail).split(" ").filter(word => word.length > 4 && !skip.has(word));
  const hits = new Set(words.filter(word => blob.has(word)));
  return hits.size >= 2 || [...hits].some(word => word.length > 5);
}

function done(reply) {
  return { reply, actions: [], quickReplies: false, flowState: null };
}

function matchSentence(variant, figureVariantIds) {
  const linked = (variant.cardedWith || []).filter(id => figureVariantIds.includes(id));
  const data = load();
  const names = (variant.cardedWith || []).map(id => {
    const fig = (data.figureVariants || []).find(item => item.id === id);
    return fig ? `${String(fig.factory).replace(/\s+guide$/i, "")} ${fig.figure}` : "";
  }).filter(Boolean);
  if (figureVariantIds.length && linked.length) {
    return `It is a correct factory match for this figure variant.`;
  }
  if (figureVariantIds.length && names.length) {
    return `It is not the accessory documented with this figure variant. It was carded with ${listNames(names.map(label => ({ label })))}.`;
  }
  if (names.length) {
    return `The guides card it with ${listNames(names.map(label => ({ label })))}.`;
  }
  return "The guides do not say which figure variant this was carded with.";
}

function conclude(variant, figureVariantIds, because) {
  return done(
    `That is the ${variantLabel(variant)}. ${because} ${matchSentence(variant, figureVariantIds)}`.replace(/\s+/g, " ").trim()
  );
}

function remain(variants, figureVariantIds) {
  return done(
    `I'm not sure which accessory variant it is. ${listNames(variants.map(variant => ({ label: variantLabel(variant) })))} still match. A plastic colour, ejector-pin mark, moulded letter, or the tip shape would settle it. ${figureVariantIds.length ? "The factory match stays open until the accessory variant is known." : ""}`.trim()
  );
}

function askTell(variants, flow) {
  const used = Array.isArray(flow.usedTells) ? flow.usedTells : [];
  const photoTells = Array.isArray(flow.photoTells) ? flow.photoTells : [];
  const picked = pickTell(variants, used);
  if (!picked) return remain(variants, flow.figureVariantIds || []);
  const seen = photoTells.length ? picked.tells.filter(tell => photoHit(tell.detail, photoTells)) : [];
  const seenSets = new Set(seen.map(tell => tell.hits.map(variant => variant.id).sort().join("|")));
  if (seen.length && seenSets.size === 1) {
    const next = seen[0].hits;
    const note = `The photo shows a match for “${seen[0].detail}”.`;
    if (next.length === 1) return conclude(next[0], flow.figureVariantIds || [], note);
    if (next.length > 1 && next.length < variants.length) {
      return askTell(next, { ...flow, usedTells: [...used, picked.category], photoTells: [] });
    }
  }
  const buttons = picked.tells.slice(0, 6).map(tell => {
    const label = tell.detail.length > 110 ? `${tell.detail.slice(0, 107).trim()}...` : tell.detail;
    return label;
  });
  const unique = [];
  for (const label of buttons) {
    if (!unique.some(item => norm(item) === norm(label))) unique.push(label);
  }
  unique.push("I'm not sure");
  return {
    reply: [
      flow.lead || `These ${variants[0].accessory} variants are still possible: ${listNames(variants.map(variant => ({ label: `${variant.factory} ${variant.mould}` })))}.`,
      "",
      picked.tells[0].where || "Look at the next detail.",
      "",
      "Which of these do you see?"
    ].join("\n"),
    actions: unique.map(label => ({ label, value: label })),
    quickReplies: true,
    flowState: {
      topic: "accessory_factory",
      step: "tell",
      accessory: variants[0].accessory,
      variantIds: variants.map(variant => variant.id),
      figure: flow.figure || "",
      factory: flow.factory || "",
      figureVariantIds: flow.figureVariantIds || [],
      usedTells: [...used, picked.category],
      photoTells,
      lead: ""
    }
  };
}

export function accessoryOffer(match) {
  if (!match || !match.figure || !match.factory) return null;
  const figureVariants = figureVariantsFor(match);
  if (!figureVariants.length) return null;
  const names = accessoriesForFigure(match.figure).filter(name =>
    variantsOf(name).some(variant => (variant.cardedWith || []).some(id => figureVariants.some(fig => fig.id === id)) || variantsOf(name).length)
  );
  const linked = names.filter(name => variantsOf(name).some(variant => (variant.cardedWith || []).some(id => figureVariants.some(fig => fig.id === id))));
  const choices = linked.length ? linked : [];
  if (!choices.length) return null;
  const base = {
    topic: "accessory_factory",
    figure: match.figure,
    factory: match.factory,
    figureVariantIds: figureVariants.map(variant => variant.id),
    photoTells: [],
    usedTells: []
  };
  if (choices.length === 1) {
    return {
      reply: `Shall I check the ${choices[0]} that came with this ${match.factory}? The accessory has its own tells, and the figure stamp alone does not identify it.`,
      actions: [
        { label: "Check the accessory", value: "yes" },
        { label: "No thanks", value: "no" }
      ],
      quickReplies: true,
      flowState: { ...base, step: "offer", accessory: choices[0] }
    };
  }
  return {
    reply: `This ${match.factory} can be checked against its accessories. Which one do you have?`,
    actions: choices.map(name => ({ label: name, value: name })),
    quickReplies: true,
    flowState: { ...base, step: "which", accessory: "" }
  };
}

export function startAccessoryIdentify(name, photoTells) {
  const accessory = findAccessory(name);
  if (!accessory) {
    return {
      reply: "Which accessory is it? Type its name, for example Rebel Blaster.",
      actions: [],
      quickReplies: false,
      flowState: {
        topic: "accessory_factory",
        step: "need_name",
        accessory: "",
        figure: "",
        factory: "",
        figureVariantIds: [],
        variantIds: [],
        usedTells: [],
        photoTells: photoTells || []
      }
    };
  }
  const variants = (load().accessoryVariants || []).filter(variant => variant.accessory === accessory && (variant.tells || []).length);
  if (variants.length <= 1 && variants.length === 1) {
    return conclude(variants[0], [], "That is the only documented variant with tells.");
  }
  if (!variants.length) return null;
  return askTell(variants, {
    accessory,
    figure: "",
    factory: "",
    figureVariantIds: [],
    usedTells: [],
    photoTells: photoTells || [],
    lead: `Let's check ${accessory}. The accessory tells identify the factory, separate from the figure.`
  });
}

export function accessoryContinue(flowState, message) {
  const text = String(message || "").trim();
  const wanted = norm(text);
  if (flowState.step === "need_name") {
    const started = startAccessoryIdentify(text, flowState.photoTells || []);
    if (!started || !started.flowState && !findAccessory(text)) {
      return done(`I haven't got factory-match tells for "${text}".`);
    }
    return started;
  }
  if (flowState.step === "offer") {
    if (wanted === "no" || wanted === "no thanks" || wanted === "n") {
      return done("All right. The figure variant stands, and the accessory was not checked.");
    }
    if (wanted !== "yes" && wanted !== "check the accessory" && wanted !== "y") {
      return done("I'm not sure. Say yes to check the accessory, or no to stop.");
    }
    const variants = (load().accessoryVariants || []).filter(variant => variant.accessory === flowState.accessory);
    return askTell(variants, {
      ...flowState,
      lead: `Let's check the ${flowState.accessory}. These variants are documented. The next tell is the one that separates the most of them.`
    });
  }
  if (flowState.step === "which") {
    const accessory = findAccessory(text);
    if (!accessory) return done(`I'm not sure. That isn't one of the accessories documented for ${flowState.figure}.`);
    const variants = (load().accessoryVariants || []).filter(variant => variant.accessory === accessory);
    return askTell(variants, { ...flowState, accessory, lead: `Let's check the ${accessory}.` });
  }
  const all = load().accessoryVariants || [];
  const variants = all.filter(variant => (flowState.variantIds || []).includes(variant.id));
  if (wanted === "i m not sure" || wanted === "im not sure") return remain(variants, flowState.figureVariantIds || []);
  const category = (flowState.usedTells || []).slice(-1)[0];
  const tell = variants.flatMap(variant => variant.tells || []).find(item =>
    item.category === category && (norm(item.detail) === wanted || norm(item.detail).startsWith(wanted.replace(/\.\.\.$/, "")))
  );
  if (!tell) return done(`I'm not sure. That isn't one of the verified tells for ${flowState.accessory}.`);
  const next = variants.filter(variant => (variant.tells || []).some(item => norm(item.detail) === norm(tell.detail)));
  if (next.length === 1) {
    return conclude(next[0], flowState.figureVariantIds || [], `“${tell.detail}” matches this mould.`);
  }
  if (!next.length) return remain(variants, flowState.figureVariantIds || []);
  return askTell(next, { ...flowState, photoTells: [] });
}
