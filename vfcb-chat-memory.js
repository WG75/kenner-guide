(function () {
  const logEl = document.getElementById("droidLog");
  const inputEl = document.getElementById("droidInput");
  const statusEl = document.getElementById("droidStatus");

  const VV_JAWA_URL = "https://www.variantvillain.com/characters/jawa/";
  const VV_JAWA_CLOAK_URL = "https://www.variantvillain.com/accessory-guide/jawa-cloak/";
  const VV_JAWA_VINYL_CAPE_URL = "https://www.variantvillain.com/accessory-guide/jawa-vinyl-cape/";
  const VV_JAWA_BLASTER_URL = "https://www.variantvillain.com/accessory-guide/jawa-blaster/";

  const state = {
    history: [],
    currentFigure: null,
    step: null,
    selectedReference: null,
    capeType: null
  };

  function normalise(text) {
    return String(text || "").trim().toLowerCase();
  }

  // 🔥 FIXED INTENT PRIORITY
  function isJawaBlasterStart(text) {
    const t = normalise(text);
    return (
      t.includes("jawa") &&
      (
        t.includes("blaster") ||
        t.includes("weapon") ||
        t.includes("accessory") ||
        t.includes("accessories")
      )
    );
  }

  function isJawaStart(text) {
    const t = normalise(text);

    // block accessory queries from triggering figure flow
    if (
      t.includes("blaster") ||
      t.includes("weapon") ||
      t.includes("accessory") ||
      t.includes("accessories")
    ) {
      return false;
    }

    return t.includes("jawa");
  }

  function appendMessage(role, text) {
    if (!logEl) return;

    const wrap = document.createElement("div");
    wrap.className = `vfcb-msg vfcb-${role}`;
    wrap.style.margin = "10px 0";
    wrap.style.padding = "12px 14px";
    wrap.style.borderRadius = "12px";
    wrap.style.lineHeight = "1.5";
    wrap.innerHTML = text.replace(/\n/g, "<br>");

    logEl.appendChild(wrap);
    logEl.scrollTop = logEl.scrollHeight;
  }

  function appendImageCard(title, imageUrl, caption) {
    if (!logEl) return;

    const card = document.createElement("div");
    card.style.margin = "12px 0";

    card.innerHTML = `
      <strong>${title}</strong><br>
      <img src="${imageUrl}" style="width:100%; border-radius:8px; margin:6px 0;">
      <div>${caption.replace(/\n/g, "<br>")}</div>
    `;

    logEl.appendChild(card);
  }

  function addUser(text) {
    appendMessage("user", text);
  }

  function addBot(text) {
    appendMessage("assistant", text);
  }

  function jawaOpening() {
    return `Yes I can do that — let's start with the cape.

Which of these does your Jawa have?

1. Vinyl cape - smooth plastic
2. Cloth cloak - fabric
3. Or neither. Just a naked figure

Just reply with 1, 2 or 3.`;
  }

  function showBlasterReference() {
    addBot(`Ok — compare your blaster with this reference:`);

    appendImageCard(
      "Jawa Blaster Reference",
      "https://www.variantvillain.com/wp-content/uploads/2021/12/JawaBlaster_000.jpg",
      `Check:
• mould shape
• rear bump
• plastic colour
• detail sharpness`
    );

    addBot(`First check: float test.

• If it sinks → repro
• If it floats → MAY be original

Important:
Modern repros can float, so this is not proof.

Most originals are dark blue.

Grey pieces:
Be careful — very common repro colour.
Rare silver Glasslite version exists, but extremely uncommon.

Full guide:
${VV_JAWA_BLASTER_URL}

Tell me:
• colour
• float result
• rear bump

and I’ll guide you.`);
    
    state.currentFigure = "jawa";
    state.step = "blaster";
  }

  function handleBlasterReply(text) {
    const t = normalise(text);

    if (t.includes("grey") || t.includes("gray") || t.includes("silver")) {
      addBot(`Be careful.

Most originals are dark blue.

Grey is commonly repro.

There IS a rare silver Glasslite version, but do not assume that.

Next:
• Do float test
• Compare exact mould vs reference

${VV_JAWA_BLASTER_URL}`);
      return;
    }

    if (t.includes("float") || t.includes("sink")) {
      addBot(`Float test rule:

• Sinks → repro
• Floats → possible original

But:
Floating does NOT confirm authenticity.

You must match mould details exactly.`);
      return;
    }

    addBot(`Check:

• rear bump shape
• mould sharpness
• plastic tone

Use:
${VV_JAWA_BLASTER_URL}`);
  }

  function showHongKongReferenceImages() {
    addBot(`Compare your leg marking and choose:`);

    appendImageCard("1. Kader M1", "/public/images/jawa_figure_kader_M1.png", "");
    appendImageCard("2. Kader M2", "/public/images/jawa_figure_kader_M2.png", "");
    appendImageCard("3. Unitoy M3", "/public/images/jawa_figure_unitoy_M3.png", "");
    appendImageCard("4. Unitoy M4", "/public/images/jawa_figure_unitoy_lili-ledy_M4.png", "");

    addBot(`Reply 1, 2, 3 or 4.`);
    state.step = "choose-reference";
  }

  function choiceReply(choice) {
    const map = {
      "1": "https://www.variantvillain.com/characters/sw/jawa/#f1",
      "2": "https://www.variantvillain.com/characters/sw/jawa/#f2",
      "3": "https://www.variantvillain.com/characters/sw/jawa/#f3",
      "4": "https://www.variantvillain.com/characters/sw/jawa/#f3"
    };

    addBot(`Closest match.

See full detail:
${map[choice]}

Do you want help with the blaster?

1 yes
2 no`);

    state.step = "blaster-choice";
  }

  function processMessage(rawMessage) {
    const message = rawMessage.trim();
    const t = normalise(message);

    addUser(message);

    // 🔥 BLASTER PRIORITY FIRST
    if (!state.currentFigure && isJawaBlasterStart(t)) {
      showBlasterReference();
      return;
    }

    if (!state.currentFigure && isJawaStart(t)) {
      state.currentFigure = "jawa";
      state.step = "cape";
      addBot(jawaOpening());
      return;
    }

    if (state.step === "cape") {
      if (t === "3") {
        state.step = "leg";
        addBot(`Check COO:

1 Hong Kong
2 no Hong Kong
3 can't tell`);
        return;
      }

      addBot(`Reply 1, 2 or 3.`);
      return;
    }

    if (state.step === "leg") {
      if (t === "1") {
        showHongKongReferenceImages();
        return;
      }
    }

    if (state.step === "choose-reference") {
      choiceReply(t);
      return;
    }

    if (state.step === "blaster-choice") {
      if (t === "1") {
        showBlasterReference();
        return;
      }

      addBot(`Anything else I can help with?`);
      return;
    }

    if (state.step === "blaster") {
      handleBlasterReply(message);
      return;
    }

    addBot("Not sure what you mean. Try again.");
  }

  window.sendDroidMessage = function () {
    const message = inputEl.value;
    inputEl.value = "";
    processMessage(message);
  };

})();