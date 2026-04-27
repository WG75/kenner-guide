// ===== EXISTING IMPORTS / SETUP (KEEP AS IS ABOVE THIS LINE) =====


// =============================
// GENERIC "GUIDE ME" HANDLER
// =============================
function isGuideMe(input) {
  const t = input.toLowerCase().trim();

  return (
    t === "4" ||
    t.includes("all of the above") ||
    t.includes("guide me") ||
    t.includes("help me") ||
    t.includes("not sure") ||
    t.includes("unsure")
  );
}


// =============================
// JAWA CLARIFICATION RESPONSE
// =============================
function jawaClarifyResponse() {
  return {
    reply: `Jawas… filthy traders, but they do carry interesting items.

Do you need help with a Jawa figure or one of its accessories?

1 Jawa figure
2 Jawa blaster
3 Jawa cloak / cape
4 All of the above — guide me

You can reply with a number or describe it in your own words.`,
    images: [],
    flowState: { mode: "jawa-clarify" }
  };
}


// =============================
// HANDLE JAWA CLARIFICATION
// =============================
function handleJawaClarify(message) {
  const t = message.toLowerCase();

  if (t === "1" || t.includes("figure")) {
    return startFlow("jawa.figure");
  }

  if (t === "2" || t.includes("blaster") || t.includes("gun") || t.includes("weapon") || t.includes("pew")) {
    return startFlow("jawa.blaster");
  }

  if (t === "3" || t.includes("cloak") || t.includes("cape") || t.includes("vinyl") || t.includes("cloth")) {
    return {
      reply: `Got it — Jawa cloak or cape.

Which one are you checking?

1 Vinyl cape - smooth plastic
2 Cloth cloak - fabric
3 Not sure

You can reply with a number or describe it in your own words.`,
      images: [],
      flowState: { mode: "jawa-cape" }
    };
  }

  if (isGuideMe(t)) {
    return {
      reply: `No problem. Let’s start with the easiest visible detail.

What does your Jawa have?

1 Vinyl cape - smooth plastic
2 Cloth cloak - fabric
3 No cape or cloak

You can reply with a number or describe it in your own words.`,
      images: [],
      flowState: { flowId: "jawa.figure", stepId: "cape_question" }
    };
  }

  return jawaClarifyResponse();
}


// =============================
// GENERIC BLASTER CLARIFICATION
// =============================
function genericBlasterClarify() {
  return {
    reply: `I found multiple blaster types in the Kenner Star Wars line.

Which one are you asking about?

1 Imperial Blaster / Stormtrooper blaster
2 Jawa Blaster
3 Princess Leia Blaster
4 Rebel Blaster / Han Solo blaster
5 All of the above — guide me

You can reply with a number or describe it in your own words.`,
    images: [],
    flowState: { mode: "blaster-clarify" }
  };
}


// =============================
// HANDLE BLASTER CLARIFICATION
// =============================
function handleBlasterClarify(message) {
  const t = message.toLowerCase();

  if (t === "1" || t.includes("imperial") || t.includes("stormtrooper")) {
    return startFlow("imperial.blaster");
  }

  if (t === "2" || t.includes("jawa")) {
    return startFlow("jawa.blaster");
  }

  if (t === "3" || t.includes("leia")) {
    return startFlow("leia.blaster");
  }

  if (t === "4" || t.includes("rebel") || t.includes("han")) {
    return startFlow("rebel.blaster");
  }

  if (isGuideMe(t)) {
    return {
      reply: `No problem. Describe the blaster you have and I’ll guide you step by step.

For example:
• small pistol
• long rifle
• has a scope
• colour

Or send a photo if available.`,
      images: [],
      flowState: {}
    };
  }

  return genericBlasterClarify();
}


// =============================
// MAIN ROUTER ADDITIONS
// =============================

// Add inside your handler:

// BEFORE flow handling:

if (flowState?.mode === "jawa-clarify") {
  return res.status(200).json(handleJawaClarify(message));
}

if (flowState?.mode === "blaster-clarify") {
  return res.status(200).json(handleBlasterClarify(message));
}


// =============================
// DETECT VAGUE JAWA
// =============================
const msg = message.toLowerCase();

if (
  msg === "jawa" ||
  msg === "jawas" ||
  msg.includes("help with jawa")
) {
  return res.status(200).json(jawaClarifyResponse());
}


// =============================
// DETECT GENERIC BLASTER
// =============================
if (
  msg === "blaster" ||
  msg.includes("gun") ||
  msg.includes("weapon")
) {
  return res.status(200).json(genericBlasterClarify());
}