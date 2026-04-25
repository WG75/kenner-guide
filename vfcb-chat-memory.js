(function () {
  const logEl = document.getElementById("droidLog");
  const inputEl = document.getElementById("droidInput");
  const statusEl = document.getElementById("droidStatus");

  const state = {
    history: [],
    currentFigure: null,
    step: null
  };

  function setStatus(text) {
    if (statusEl) statusEl.textContent = text || "";
  }

  function appendMessage(role, text) {
    const div = document.createElement("div");
    div.className = role === "user" ? "user-msg" : "bot-msg";
    div.innerText = text;
    logEl.appendChild(div);
    logEl.scrollTop = logEl.scrollHeight;
  }

  function addUser(text) {
    appendMessage("user", text);
  }

  function addBot(text) {
    appendMessage("assistant", text);
  }

  function normalise(t) {
    return String(t || "").toLowerCase().trim();
  }

  function detectCape(msg) {
    const t = normalise(msg);

    if (t === "1" || t.includes("vinyl")) return "vinyl";
    if (t === "2" || t.includes("cloth")) return "cloth";
    if (t === "3" || t.includes("no cape") || t.includes("naked")) return "none";

    return null;
  }

  function isNoCoo(msg) {
    const t = normalise(msg);

    return (
      t.includes("gmfgi") ||
      t.includes("cmfg 1977") ||
      (
        t.includes("1977") &&
        !t.includes("hong kong") &&
        (t.includes("hard to tell") || t.includes("looks like"))
      )
    );
  }

  function isHongKong(msg) {
    return normalise(msg).includes("hong kong");
  }

  function jawaStart() {
    return `Yes I can do that — let's start with the cape.

Which of these does your Jawa have?

1. Vinyl cape - smooth plastic
2. Cloth cloak - fabric
3. Or neither. Just a naked figure

Just tell me: vinyl, cloth, or missing cloak.
Or you can reply with 1, 2 or 3.`;
  }

  function jawaNoCape() {
    return `Right — so your Jawa is missing its cape.

That’s common.

Next step:
Check the COO marking on the legs.

What does it say?`;
  }

  function noCooReply() {
    return `If there’s no Hong Kong marking on the leg, you’re looking at a Kader China variant.

It will read:
© G.M.F.G.I. 1977

This variant was paired with:
• M2 Jawa blaster (short bump)
• Smooth cloth cloak

Two variants exist, based on copyright text size.

Next checks:
• bandolier tone
• eye colour`;
  }

  function hongKongReply() {
    return `Good — Hong Kong COO.

This is where most Jawa variants sit.

Next step:
We need to narrow it down using figure traits.

Check:

• Eye colour (bright yellow / dull / orange tone)
• Bandolier (shape + colour tone)
• Cloak type (if present)
• Blaster mould (if present)

Hong Kong Jawas have multiple factory variations, so COO alone is not enough.

Tell me what you see for eye colour and bandolier.`;
  }

  async function processMessage(msg) {
    const t = normalise(msg);

    addUser(msg);

    if (!state.currentFigure && t.includes("jawa")) {
      state.currentFigure = "jawa";
      state.step = "cape";
      addBot(jawaStart());
      return;
    }

    if (state.step === "cape") {
      const cape = detectCape(msg);

      if (!cape) {
        addBot("Reply with 1, 2 or 3.");
        return;
      }

      state.step = "coo";

      if (cape === "none") {
        addBot(jawaNoCape());
        return;
      }

      addBot("Next step: check COO marking on the legs.");
      return;
    }

    if (state.step === "coo") {
      if (isNoCoo(msg)) {
        addBot(noCooReply());
        return;
      }

      if (isHongKong(msg)) {
        state.step = "hk-detail";
        addBot(hongKongReply());
        return;
      }

      addBot("I need to know what the leg marking says — Hong Kong, Taiwan, or just 1977?");
      return;
    }

    addBot("Tell me more about the figure.");
  }

  window.sendDroidMessage = function () {
    const msg = inputEl.value;
    inputEl.value = "";
    processMessage(msg);
  };

})();
