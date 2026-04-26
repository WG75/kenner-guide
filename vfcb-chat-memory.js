(function () {
  const logEl = document.getElementById("droidLog");
  const inputEl = document.getElementById("droidInput");

  const VV_JAWA_BLASTER_URL = "https://www.variantvillain.com/accessory-guide/jawa-blaster/";

  const state = {
    currentFigure: null,
    step: null
  };

  function normalise(text) {
    return String(text || "").trim().toLowerCase();
  }

  function appendMessage(role, text) {
    const div = document.createElement("div");
    div.innerHTML = text.replace(/\n/g, "<br>");
    logEl.appendChild(div);
    logEl.scrollTop = logEl.scrollHeight;
  }

  function addUser(t) {
    appendMessage("user", t);
  }

  function addBot(t) {
    appendMessage("bot", t);
  }

  function appendImage(src) {
    const img = document.createElement("img");
    img.src = src;
    img.style.width = "100%";
    img.style.margin = "10px 0";
    logEl.appendChild(img);
  }

  // 🔥 FINAL INTENT DETECTION
  function isBlasterIntent(text) {
    const t = normalise(text);

    return (
      t.includes("jawa") &&
      (
        t.includes("blaster") ||
        t.includes("gun") ||
        t.includes("pistol") ||
        t.includes("weapon") ||
        t.includes("accessory") ||
        t.includes("laser") ||
        t.includes("ray") ||
        t.includes("pew")
      )
    );
  }

  function isJawaFigureIntent(text) {
    const t = normalise(text);

    if (
      t.includes("blaster") ||
      t.includes("gun") ||
      t.includes("pistol") ||
      t.includes("weapon") ||
      t.includes("accessory") ||
      t.includes("laser") ||
      t.includes("ray") ||
      t.includes("pew")
    ) {
      return false;
    }

    return t.includes("jawa");
  }

  function showBlasterStart() {
    addBot(`Ok — compare your blaster with this reference:`);

    appendImage("https://www.variantvillain.com/wp-content/uploads/2021/12/JawaBlaster_000.jpg");

    addBot(`Check:
• mould shape
• rear bump
• plastic colour
• detail sharpness

Can you identify it against the reference image?

Reply with:

1 Yes
2 No
3 Not sure`);

    state.step = "blaster-image";
    state.currentFigure = "jawa";
  }

  function askFloat() {
    addBot(`Next check: float test.

• If it sinks → reproduction
• If it floats → MAY be original

Important:
Modern reproductions can float, so this is not proof.

Does yours sink or float?

Reply with:

1 float
2 sink`);

    state.step = "blaster-float";
  }

  function askColour() {
    addBot(`Good. Now check the colour.

Most original Jawa blasters are dark blue or black-blue tones.

Reply with:

1 dark blue / black-blue
2 black
3 grey
4 silver
5 not sure`);

    state.step = "blaster-colour";
  }

  function handleColour(msg) {
    const t = normalise(msg);

    if (t.includes("3") || t.includes("grey")) {
      addBot(`Grey pieces:
Be careful — very common repro colour.

There are rare silver Glasslite versions, but extremely uncommon.

Best to check:
${VV_JAWA_BLASTER_URL}`);
      return;
    }

    if (t.includes("2") || t.includes("black")) {
      addBot(`Black needs caution.

Could be:
• repro
• modern
• very dark blue mistaken

Compare carefully:
${VV_JAWA_BLASTER_URL}`);
      return;
    }

    if (t.includes("1") || t.includes("blue")) {
      addBot(`Good — most originals fall in this range.

Still confirm:
• mould
• rear bump
• sharpness

Use:
${VV_JAWA_BLASTER_URL}`);
      return;
    }

    if (t.includes("4") || t.includes("silver")) {
      addBot(`Silver is unusual.

There is a rare Glasslite version, but extremely uncommon.

Do not assume without exact match.

Check:
${VV_JAWA_BLASTER_URL}`);
      return;
    }

    addBot(`Compare using:
${VV_JAWA_BLASTER_URL}`);
  }

  function process(msg) {
    addUser(msg);
    const t = normalise(msg);

    // 🔥 ALWAYS override with blaster intent
    if (isBlasterIntent(t)) {
      showBlasterStart();
      return;
    }

    if (!state.currentFigure && isJawaFigureIntent(t)) {
      state.currentFigure = "jawa";
      state.step = "cape";

      addBot(`Let's start with the cape.

1 vinyl
2 cloth
3 none`);
      return;
    }

    if (state.step === "blaster-image") {
      askFloat();
      return;
    }

    if (state.step === "blaster-float") {
      if (t.includes("2") || t.includes("sink")) {
        addBot("If it sinks → reproduction.");
        state.step = null;
        state.currentFigure = null;
        return;
      }

      askColour();
      return;
    }

    if (state.step === "blaster-colour") {
      handleColour(msg);
      state.step = null;
      state.currentFigure = null;
      return;
    }

    addBot("Not sure — try asking about a Jawa or blaster.");
  }

  window.sendDroidMessage = function () {
    const msg = inputEl.value;
    inputEl.value = "";
    process(msg);
  };
})();