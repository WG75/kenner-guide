(function () {
  const logEl = document.getElementById("droidLog");
  const inputEl = document.getElementById("droidInput");
  const statusEl = document.getElementById("droidStatus");

  const state = {
    history: [],
    currentFigure: null,
    step: null,
    cooExplained: false
  };

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

  function cooIntro() {
    return `Check the Country of Origin (COO) markings on the legs.

Original vintage figures usually have:
• Hong Kong
• China
• Taiwan
• or no COO marking

Some say "Made in" followed by the country, others just list the country name.

What does your figure say?`;
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
    if (!state.cooExplained) {
      state.cooExplained = true;
      return `Right — so your Jawa is missing its cape.

That’s common.

${cooIntro()}`;
    }

    return `Right — so your Jawa is missing its cape.

Next step: check the COO marking on the legs.

What does it say?`;
  }

  function jawaCloth() {
    if (!state.cooExplained) {
      state.cooExplained = true;
      return `Good — cloth cloak.

${cooIntro()}`;
    }

    return `Good — cloth cloak.

Next step: check the COO marking on the legs.

What does it say?`;
  }

  function jawaVinyl() {
    if (!state.cooExplained) {
      state.cooExplained = true;
      return `Vinyl cape — early production.

${cooIntro()}`;
    }

    return `Vinyl cape — early production.

Next step: check the COO marking on the legs.

What does it say?`;
  }

  function noCooReply() {
    return `If there’s no Hong Kong marking on the leg, you’re looking at a Kader China variant.

It will have just one line of text reading:
© G.M.F.G.I. 1977

That stands for General Mills Fun Group Incorporated, with 1977 being the year the figure was originally licensed.

This variant was originally paired with:
• an M2 Kader Jawa Blaster (short rear bump)
• a small hood, smooth cloth cloak

KADER (CHINA) NO COO Jawas should have:

• Rectangular dark brown bandolier  
• Round yellow eyes  
• Smooth cloth cloak  

or

• Rectangular, very dark brown bandolier  
• Round yellow eyes  
• Smooth cloth cloak  

There are two variants within this Kader China NO COO version.

The most noticeable difference is the size of the copyright text on the back of the leg.

Next useful checks:
• bandolier tone  
• eye colour`;
  }

  function hongKongReply() {
    return `Good — Hong Kong COO.

This is where most Jawa variants sit.

Next step:
We need to narrow it down using figure traits.

Check:

• Eye colour  
• Bandolier (shape + tone)  
• Cloak type  
• Blaster mould  

COO alone is not enough.

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

      if (cape === "cloth") {
        addBot(jawaCloth());
        return;
      }

      if (cape === "vinyl") {
        addBot(jawaVinyl());
        return;
      }
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
