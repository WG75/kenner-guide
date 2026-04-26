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
        t.includes("pew") ||
        t.includes("shooter")
      )
    );
  }

  function isJawaMention(text) {
    return normalise(text).includes("jawa");
  }

  function showClarification() {
    addBot(`Not sure what you mean.

Did you want help with:

1. Jawa blaster (weapon)
2. Jawa figure
3. Jawa cloak / cape

Reply with 1, 2 or 3.`);

    state.step = "clarify";
  }

  function showBlasterStart() {
    addBot("Ok — compare your blaster with this reference:");

    appendImage("https://www.variantvillain.com/wp-content/uploads/2021/12/JawaBlaster_000.jpg");

    addBot(`Check:
• mould shape
• rear bump
• plastic colour
• detail sharpness

Can you identify it?

Reply:

1 Yes
2 No
3 Not sure`);

    state.step = "blaster-image";
    state.currentFigure = "jawa";
  }

  function askFloat() {
    addBot(`Next check: float test.

1 float
2 sink`);

    state.step = "blaster-float";
  }

  function askColour() {
    addBot(`Now check colour:

1 dark blue
2 black
3 grey
4 silver
5 not sure`);

    state.step = "blaster-colour";
  }

  function handleColour(t) {
    if (t === "1") {
      addBot(`Good — typical original range.

Check:
${VV_JAWA_BLASTER_URL}`);
      return;
    }

    if (t === "2") {
      addBot(`Black needs caution.

Compare:
${VV_JAWA_BLASTER_URL}`);
      return;
    }

    if (t === "3") {
      addBot(`Grey is commonly repro.

Check:
${VV_JAWA_BLASTER_URL}`);
      return;
    }

    if (t === "4") {
      addBot(`Silver is rare Glasslite.

Verify carefully:
${VV_JAWA_BLASTER_URL}`);
      return;
    }

    addBot(`Compare:
${VV_JAWA_BLASTER_URL}`);
  }

  function process(msg) {
    addUser(msg);
    const t = normalise(msg);

    // 🔥 Intent first
    if (isBlasterIntent(t)) {
      showBlasterStart();
      return;
    }

    // 🔥 Jawa but unclear meaning
    if (!state.step && isJawaMention(t)) {
      showClarification();
      return;
    }

    // clarification step
    if (state.step === "clarify") {
      if (t === "1") {
        showBlasterStart();
        return;
      }

      if (t === "2") {
        addBot("Let's identify your Jawa figure. Start with the cape.");
        state.step = null;
        return;
      }

      if (t === "3") {
        addBot("Check your cloak vs Variant Villain guide.");
        state.step = null;
        return;
      }

      addBot("Reply with 1, 2 or 3.");
      return;
    }

    // blaster flow
    if (state.step === "blaster-image") {
      askFloat();
      return;
    }

    if (state.step === "blaster-float") {
      if (t === "2") {
        addBot("If it sinks → reproduction.");
        state.step = null;
        return;
      }

      if (t === "1") {
        askColour();
        return;
      }

      addBot("Reply 1 or 2.");
      return;
    }

    if (state.step === "blaster-colour") {
      handleColour(t);
      state.step = null;
      return;
    }

    addBot("Try asking about a Jawa figure or blaster.");
  }

  window.sendDroidMessage = function () {
    const msg = inputEl.value;
    inputEl.value = "";
    process(msg);
  };
})();