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

  function setStatus(text) {
    if (statusEl) statusEl.textContent = text || "";
  }

  function escapeHtml(text) {
    return String(text || "")
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;");
  }

  function formatText(text) {
    return escapeHtml(text).replace(/\n/g, "<br>");
  }

  function appendMessage(role, text) {
    if (!logEl) return;

    const wrap = document.createElement("div");
    wrap.className = `vfcb-msg vfcb-${role}`;
    wrap.style.margin = "10px 0";
    wrap.style.padding = "12px 14px";
    wrap.style.borderRadius = "12px";
    wrap.style.lineHeight = "1.5";

    wrap.innerHTML = formatText(text);
    logEl.appendChild(wrap);
    logEl.scrollTop = logEl.scrollHeight;
  }

  function addUser(text) {
    appendMessage("user", text);
    state.history.push({ role: "user", content: text });
  }

  function addBot(text) {
    appendMessage("assistant", text);
    state.history.push({ role: "assistant", content: text });
  }

  function normalise(text) {
    return String(text || "").trim().toLowerCase();
  }

  function isJawaStart(text) {
    const t = normalise(text);
    return t.includes("jawa");
  }

  function detectCapeAnswer(text) {
    const t = normalise(text);

    if (t === "1" || t.includes("vinyl")) return "vinyl";
    if (t === "2" || t.includes("cloth")) return "cloth";
    if (
      t === "3" ||
      t.includes("no cape") ||
      t.includes("missing cape") ||
      t.includes("missing cloak") ||
      t.includes("naked") ||
      t.includes("no covering")
    ) {
      return "none";
    }

    return null;
  }

  function looksLikeNoCooJawa(text) {
    const t = normalise(text);

    if (
      t.includes("g.m.f.g.i") ||
      t.includes("gmfgi") ||
      t.includes("cmfg 1977") ||
      t.includes("gmfgi 1977")
    ) {
      return true;
    }

    return (
      t.includes("1977") &&
      !t.includes("hong kong") &&
      !t.includes("taiwan") &&
      !t.includes("macau") &&
      !t.includes("china") &&
      (
        t.includes("hard to tell") ||
        t.includes("looks like") ||
        t.includes("just says") ||
        t.includes("only says") ||
        t.includes("cant see")
      )
    );
  }

  function isHongKong(text) {
    return normalise(text).includes("hong kong");
  }

  function isTaiwan(text) {
    return normalise(text).includes("taiwan");
  }

  function isCooQuestion(text) {
    const t = normalise(text);
    return (
      t === "coo" ||
      t.includes("what is coo") ||
      t.includes("what's coo") ||
      t.includes("whats coo") ||
      t.includes("what does coo mean")
    );
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

  function jawaOpening() {
    return `Yes I can do that — let's start with the cape.

Which of these does your Jawa have?

1. Vinyl cape - smooth plastic
2. Cloth cloak - fabric
3. Or neither. Just a naked figure

Just tell me: vinyl, cloth, or missing cloak.
Or you can reply with 1, 2 or 3.`;
  }

  function jawaNoCapeReply() {
    return `Right — so your Jawa is missing its cape, what collectors would usually call a naked figure.

That’s common, so we identify it from the figure itself.

Next step:
${cooIntro()}

After that, we confirm it using:
• mould / sculpt
• plastic colour
• eye paint
• bandolier shape and tone
• and any remaining accessories

Do not rely on COO alone — mould, paint colour, plastic colour and figure assembly traits are also needed to confirm origin.`;
  }

  function jawaClothReply() {
    return `Good — so we're dealing with a cloth cloak Jawa.

Next step:
${cooIntro()}

After that, the next useful things are:
• hood size and shape
• stitching / construction
• eye colour
• bandolier shape and tone
• and whether the blaster is present

Do not rely on COO alone — mould, paint colour, plastic colour and figure assembly traits are also needed to confirm origin.`;
  }

  function jawaVinylReply() {
    return `Good — that means you have the early vinyl cape version.

Next step:
${cooIntro()}

Then we confirm it properly using:
• body sculpt
• plastic colour
• paint details
• and the correct blaster pairing

Do not rely on COO alone — mould, paint colour, plastic colour and figure assembly traits are also needed to confirm origin.`;
  }

  function cooMeaningReply() {
    return `COO means Country of Origin.

It is the country marking usually found on the legs of vintage figures, such as Hong Kong, China, Taiwan, or no COO marking.

Some figures say "Made in" followed by the country. Others just list the country name.

For Jawas, COO is useful, but not enough on its own. You still need to check:
• mould / sculpt
• eye colour
• plastic colour
• bandolier shape and tone
• cloak or blaster pairing, if present`;
  }

  function noCooKaderReply() {
    return `If there’s no Hong Kong marking on the leg, you’re looking at a Kader China variant.

M2 Kader China on Variant Villain.

It will have just one line of text reading:
© G.M.F.G.I. 1977

That stands for General Mills Fun Group Incorporated, with 1977 being the year the figure was originally licensed.

This variant was originally paired with:
• an M2 Kader Jawa Blaster - short rear bump
• a small hood, smooth cloth cloak

KADER (CHINA) No COO Jawas should have:

• Rectangular dark brown bandolier
• Round yellow eyes
• Smooth cloth cloak

or

• Rectangular, very dark brown bandolier
• Round yellow eyes
• Smooth cloth cloak

There are two variants within this Kader China No COO version.

The most noticeable difference is the size of the copyright text on the back of the leg.

Next useful checks:
• bandolier tone
• eye colour`;
  }

  function hongKongReply() {
    return `Good — Hong Kong COO.

This is where most Jawa variants sit, so we need to narrow it down using figure traits.

Next checks:
• eye colour
• bandolier shape and tone
• plastic colour
• cloak type, if present
• blaster mould, if present

COO alone is not enough.

Tell me what you can see for the eye colour and bandolier.`;
  }

  function taiwanReply() {
    return `Good — Taiwan COO.

Next checks:
• eye colour
• bandolier shape and tone
• plastic colour
• cloak type, if present
• blaster mould, if present

COO is useful, but not enough on its own.

Tell me what you can see for the eye colour and bandolier.`;
  }

  async function askApi(message) {
    setStatus("Thinking...");

    const res = await fetch("/api/chat", {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({
        message,
        history: state.history.slice(-12)
      })
    });

    const data = await res.json();
    setStatus("");

    if (!res.ok) {
      throw new Error(data?.error || "API error");
    }

    return data?.reply || "Sorry, there was a problem getting an answer.";
  }

  async function processMessage(rawMessage) {
    const message = String(rawMessage || "").trim();
    if (!message) return;

    addUser(message);

    const t = normalise(message);

    if (!state.currentFigure && isJawaStart(t)) {
      state.currentFigure = "jawa";
      state.step = "cape";
      addBot(jawaOpening());
      return;
    }

    if (state.currentFigure === "jawa" && state.step === "cape") {
      const cape = detectCapeAnswer(t);

      if (!cape) {
        addBot("Just reply with 1, 2 or 3 — or vinyl, cloth, or missing cloak.");
        return;
      }

      state.step = "coo";

      if (cape === "none") {
        addBot(jawaNoCapeReply());
        return;
      }

      if (cape === "cloth") {
        addBot(jawaClothReply());
        return;
      }

      if (cape === "vinyl") {
        addBot(jawaVinylReply());
        return;
      }
    }

    if (state.currentFigure === "jawa" && state.step === "coo") {
      if (isCooQuestion(t)) {
        addBot(cooMeaningReply());
        return;
      }

      if (looksLikeNoCooJawa(t)) {
        state.step = "confirm-kader";
        addBot(noCooKaderReply());
        return;
      }

      if (isHongKong(t)) {
        state.step = "hk-detail";
        addBot(hongKongReply());
        return;
      }

      if (isTaiwan(t)) {
        state.step = "taiwan-detail";
        addBot(taiwanReply());
        return;
      }

      addBot("I need to know what the Country of Origin (COO) marking says — Hong Kong, Taiwan, or just the copyright line such as © G.M.F.G.I. 1977?");
      return;
    }

    try {
      const reply = await askApi(message);
      addBot(reply);
    } catch (err) {
      console.error(err);
      addBot("Something went wrong getting a response.");
    }
  }

  window.sendDroidMessage = function sendDroidMessage() {
    if (!inputEl) return;
    const message = inputEl.value.trim();
    inputEl.value = "";
    processMessage(message);
  };

  window.useDroidPrompt = function useDroidPrompt(promptText) {
    if (!promptText) return;
    processMessage(promptText);
  };

  if (inputEl) {
    inputEl.addEventListener("keydown", function (e) {
      if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        window.sendDroidMessage();
      }
    });
  }
})();
