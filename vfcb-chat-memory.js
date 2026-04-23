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
    wrap.style.whiteSpace = "normal";

    if (role === "user") {
      wrap.style.background = "rgba(255, 184, 0, 0.12)";
      wrap.style.border = "1px solid rgba(255, 184, 0, 0.35)";
      wrap.style.color = "#f5f5f5";
    } else {
      wrap.style.background = "rgba(255,255,255,0.04)";
      wrap.style.border = "1px solid rgba(255,255,255,0.08)";
      wrap.style.color = "#f5f5f5";
    }

    wrap.innerHTML = formatText(text);
    logEl.appendChild(wrap);
    logEl.scrollTop = logEl.scrollHeight;
  }

  function pushHistory(role, content) {
    state.history.push({ role, content });
    if (state.history.length > 12) {
      state.history = state.history.slice(-12);
    }
  }

  function addBot(text) {
    appendMessage("assistant", text);
    pushHistory("assistant", text);
  }

  function addUser(text) {
    appendMessage("user", text);
    pushHistory("user", text);
  }

  function normalise(text) {
    return String(text || "").trim().toLowerCase();
  }

  function isJawaStart(msg) {
    return normalise(msg).includes("jawa");
  }

  function isCooQuestion(msg) {
    const t = normalise(msg);
    return (
      t === "coo" ||
      t.includes("what's coo") ||
      t.includes("whats coo") ||
      t.includes("what does coo mean")
    );
  }

  function detectCapeAnswer(msg) {
    if (!msg) return null;

    const m = String(msg).trim().toLowerCase();

    if (m === "1") return "vinyl";
    if (m === "2") return "cloth";
    if (m === "3") return "none";

    if (m.includes("vinyl")) return "vinyl";
    if (m.includes("cloth") || m.includes("fabric")) return "cloth";

    if (
      m.includes("none") ||
      m.includes("no cape") ||
      m.includes("missing cloak") ||
      m.includes("missing cape") ||
      m.includes("naked") ||
      m.includes("no covering")
    ) {
      return "none";
    }

    return null;
  }

  function looksLikeNoCooJawa(msg) {
    const t = normalise(msg);

    return (
      t.includes("g.m.f.g.i") ||
      t.includes("gmfgi") ||
      t.includes("cmfg 1977") ||
      t.includes("gmfgi 1977") ||
      (
        t.includes("1977") &&
        !t.includes("hong kong") &&
        !t.includes("taiwan") &&
        !t.includes("macau") &&
        !t.includes("china") &&
        (t.includes("hard to tell") || t.includes("looks like") || t.includes("just says"))
      )
    );
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
Check the COO marking on the legs.

Then we confirm it using:
• mould / sculpt
• plastic colour
• eye paint
• bandolier shape and tone
• and any remaining accessories

Do not rely on COO alone — mould, paint colour, plastic colour and figure assembly traits are also needed to confirm origin.

What does the leg marking say?`;
  }

  function jawaClothReply() {
    return `Good — so we're dealing with a cloth cloak Jawa.

Next step:
Check the COO marking on the legs.

After that, the next useful things are:
• hood size and shape
• stitching / construction
• eye colour
• bandolier shape and tone
• and whether the blaster is present

Do not rely on COO alone — mould, paint colour, plastic colour and figure assembly traits are also needed to confirm origin.

What does the leg marking say?`;
  }

  function jawaVinylReply() {
    return `Good — that means you have the early vinyl cape version.

Next step:
Check the COO marking on the legs.

Then we confirm it properly using:
• body sculpt
• plastic colour
• paint details
• and the correct blaster pairing

Do not rely on COO alone — mould, paint colour, plastic colour and figure assembly traits are also needed to confirm origin.

What does the leg marking say?`;
  }

  function cooMeaningReply() {
    return `COO means Country of Origin.

That is the country marking usually found on the legs of vintage figures, such as Hong Kong or Taiwan.

On Jawas, COO is a very useful starting point — but not enough on its own.

To confirm a Jawa properly, you also need to check:
• mould / sculpt
• eye colour
• plastic colour
• bandolier shape and tone
• and cloak or blaster pairing if present.`;
  }

  function noCooKaderReply() {
    return `If you can't see Hong Kong on the leg, you must have a Kader China variant.

It will have just one line of text reading:
© G.M.F.G.I. 1977

That stands for General Mills Fun Group Incorporated, with 1977 being the year the figure was originally licensed.

KADER (CHINA) NCOO should be:

• Rectangular dark brown bandolier
• Round yellow eyes
• Smooth cloth cloak

or

• Rectangular, very dark brown bandolier
• Round yellow eyes
• Smooth cloth cloak

Paired with an M2 Kader Jawa Blaster — the one with the short bump.

There are two variants within this Kader China NCOO version.
The difference is the size of the copyright text on the back of the leg.

If you want, next send:
• a close photo of the back of the legs
• a front photo of the figure
• and the cloak hood if present

That will let me narrow down which of the two Kader China NCOO variants it is.`;
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
        history: state.history
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
    const msg = inputEl.value.trim();
    inputEl.value = "";
    processMessage(msg);
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
