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

  function append(text) {
    const div = document.createElement("div");
    div.innerHTML = text.replace(/\n/g, "<br>");
    logEl.appendChild(div);
    logEl.scrollTop = logEl.scrollHeight;
  }

  function addUser(t) {
    append(t);
  }

  function addBot(t) {
    append(t);
  }

  function appendImage(src) {
    const img = document.createElement("img");
    img.src = src;
    img.style.width = "100%";
    img.style.margin = "10px 0";
    logEl.appendChild(img);
  }

  // 🔥 Intent detection
  function isBlasterIntent(text) {
    const t = normalise(text);
    return (
      t.includes("jawa") &&
      (
        t.includes("blaster") ||
        t.includes("gun") ||
        t.includes("pistol") ||
        t.includes("weapon") ||
        t.includes("laser") ||
        t.includes("ray") ||
        t.includes("pew")
      )
    );
  }

  function showBlasterStart() {
    addBot("Ok — compare your blaster with this reference:");

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
Modern repros can float, so this is not proof.

Does yours sink or float?

Reply with:

1 float
2 sink`);

    state.step = "blaster-float";
  }

  function askColour() {
    addBot(`Good. Now check the colour.

Reply with:

1 dark blue / black-blue
2 black
3 grey
4 silver
5 not sure`);

    state.step = "blaster-colour";
  }

  function handleColour(t) {
    if (t === "1") {
      addBot(`Good — most originals fall in this range.

Still confirm mould + bump:

${VV_JAWA_BLASTER_URL}`);
      return;
    }

    if (t === "2") {
      addBot(`Black needs caution.

Could be:
• repro
• modern
• very dark blue mistaken

Compare:
${VV_JAWA_BLASTER_URL}`);
      return;
    }

    if (t === "3") {
      addBot(`Grey pieces:
Very common repro colour.

Check:
${VV_JAWA_BLASTER_URL}`);
      return;
    }

    if (t === "4") {
      addBot(`Silver is rare Glasslite.

Do not assume without exact match.

Check:
${VV_JAWA_BLASTER_URL}`);
      return;
    }

    addBot(`Compare carefully:
${VV_JAWA_BLASTER_URL}`);
  }

  function process(msg) {
    addUser(msg);
    const t = normalise(msg);

    // 🔥 override always
    if (isBlasterIntent(t)) {
      showBlasterStart();
      return;
    }

    // STEP 1 → IMAGE CHECK
    if (state.step === "blaster-image") {
      // no matter what they answer → move forward
      askFloat();
      return;
    }

    // STEP 2 → FLOAT
    if (state.step === "blaster-float") {
      if (t === "2" || t.includes("sink")) {
        addBot("If it sinks → reproduction.");
        state.step = null;
        state.currentFigure = null;
        return;
      }

      if (t === "1" || t.includes("float")) {
        askColour();
        return;
      }

      addBot("Reply with 1 (float) or 2 (sink)");
      return;
    }

    // STEP 3 → COLOUR
    if (state.step === "blaster-colour") {
      handleColour(t);
      state.step = null;
      state.currentFigure = null;
      return;
    }

    addBot("Ask about a Jawa or blaster to get started.");
  }

  window.sendDroidMessage = function () {
    const msg = inputEl.value;
    inputEl.value = "";
    process(msg);
  };
})();