(function () {
  const logEl = document.getElementById("droidLog");
  const inputEl = document.getElementById("droidInput");
  const statusEl = document.getElementById("droidStatus");

  const VV_JAWA_URL = "https://www.variantvillain.com/characters/jawa/";

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
    wrap.innerHTML = formatText(text);

    logEl.appendChild(wrap);
    logEl.scrollTop = logEl.scrollHeight;
  }

  function appendImageCard(title, imageUrl, caption) {
    if (!logEl) return;

    const card = document.createElement("div");
    card.className = "vfcb-image-card";
    card.style.margin = "12px 0";
    card.style.padding = "12px";
    card.style.borderRadius = "12px";
    card.style.border = "1px solid rgba(255,255,255,0.15)";
    card.style.background = "rgba(255,255,255,0.04)";

    const heading = document.createElement("div");
    heading.textContent = title;
    heading.style.fontWeight = "700";
    heading.style.marginBottom = "8px";

    const img = document.createElement("img");
    img.src = imageUrl;
    img.alt = title;
    img.loading = "lazy";
    img.style.width = "100%";
    img.style.maxWidth = "100%";
    img.style.borderRadius = "10px";
    img.style.display = "block";
    img.style.marginBottom = "8px";

    const note = document.createElement("div");
    note.innerHTML = formatText(caption);
    note.style.lineHeight = "1.45";

    card.appendChild(heading);
    card.appendChild(img);
    card.appendChild(note);

    logEl.appendChild(card);
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
    return normalise(text).includes("jawa");
  }

  function detectCapeAnswer(text) {
    const t = normalise(text);

    if (t === "1" || t.includes("vinyl")) return "vinyl";
    if (t === "2" || t.includes("cloth") || t.includes("fabric")) return "cloth";

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

  function detectLegMarkingAnswer(text) {
    const t = normalise(text);

    if (t === "1" || t.includes("hong kong")) return "hong-kong";

    if (
      t === "2" ||
      t.includes("no hong kong") ||
      t.includes("no coo") ||
      t.includes("no country") ||
      t.includes("just copyright") ||
      t.includes("only copyright") ||
      t.includes("just 1977") ||
      t.includes("only 1977") ||
      t.includes("g.m.f.g.i") ||
      t.includes("gmfgi") ||
      t.includes("cmfg")
    ) {
      return "no-coo";
    }

    if (
      t === "3" ||
      t.includes("can't tell") ||
      t.includes("cant tell") ||
      t.includes("doesn't appear") ||
      t.includes("doesnt appear") ||
      t.includes("neither") ||
      t.includes("repro") ||
      t.includes("bootleg") ||
      t.includes("retro")
    ) {
      return "unclear";
    }

    return null;
  }

  function detectReferenceChoice(text) {
    const t = normalise(text);

    if (t === "1" || t.includes("kader m1")) return "kader-m1";
    if (t === "2" || t.includes("kader m2")) return "kader-m2";
    if (t === "3" || t.includes("unitoy m3")) return "unitoy-m3";
    if (t === "4" || t.includes("lili ledy") || t.includes("unitoy/lili")) return "unitoy-lili-ledy-m4";

    return null;
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

  function jawaLegQuestion(capeType) {
    if (capeType === "none") {
      return `Right — so your Jawa is missing its cape, what collectors often refer to as a naked figure.

In that case, let's identify the figure itself.

Next step:
Check the Country of Origin (COO) markings on the legs.

Vintage Jawas should show:
© G.M.F.G.I. 1977 on top, with HONG KONG underneath

or just:
© G.M.F.G.I. 1977

Reply with:

1 for Hong Kong
2 if it doesn't show Hong Kong
3 if you can't tell / it doesn't appear to have either`;
    }

    if (capeType === "cloth") {
      return `Good — so we're dealing with a cloth cloak Jawa.

Next step:
Check the Country of Origin (COO) markings on the legs.

Vintage Jawas should show:
© G.M.F.G.I. 1977 on top, with HONG KONG underneath

or just:
© G.M.F.G.I. 1977

Reply with:

1 for Hong Kong
2 if it doesn't show Hong Kong
3 if you can't tell / it doesn't appear to have either`;
    }

    if (capeType === "vinyl") {
      return `Good — that means you may have the early vinyl cape version.

Next step:
Check the Country of Origin (COO) markings on the legs.

Vintage Jawas should show:
© G.M.F.G.I. 1977 on top, with HONG KONG underneath

or just:
© G.M.F.G.I. 1977

Reply with:

1 for Hong Kong
2 if it doesn't show Hong Kong
3 if you can't tell / it doesn't appear to have either`;
    }

    return "";
  }

  function noCooKaderReply() {
    addBot(`That points to the Kader China M2 No COO Jawa.

It should show just:
© G.M.F.G.I. 1977

No HONG KONG underneath.

G.M.F.G.I. stands for General Mills Fun Group Incorporated, with 1977 being the year the figure was originally licensed.

Compare your leg marking with this reference:`);

    appendImageCard(
      "Kader China M2 No COO",
      "/public/images/jawa_figure_kader_china_M2.png",
      `Kader China M2 2a and M2 2b:
Only © G.M.F.G.I. 1977. No HONG KONG marking.

Notice the size difference between 2a and 2b, and how the 2a version's text aligns with the fold.`
    );

    addBot(`This variant was originally paired with:
• an M2 Kader Jawa Blaster - short rear bump
• a small hood, smooth cloth cloak

Kader China M2 No COO Jawas should have:

• Rectangular dark brown bandolier
• Round yellow eyes
• Smooth cloth cloak

or

• Rectangular, very dark brown bandolier
• Round yellow eyes
• Smooth cloth cloak

Important:
DON’T RELY ON JUST THE COO TO IDENTIFY A FIGURE. Mould, paint colour, plastic colour and figure assembly traits are also needed to confirm your figure’s origins.

Full Jawa guide on Variant Villain:
${VV_JAWA_URL}`);
  }

  function showHongKongReferenceImages() {
    addBot(`Ok, compare your left-leg marking with these reference images and choose the closest match.

Reply with:

1 for Kader M1
2 for Kader M2
3 for Unitoy M3
4 for Unitoy / Lili Ledy M4`);

    appendImageCard(
      "1. Kader M1",
      "/public/images/jawa_figure_kader_M1.png",
      `Kader M1 1a:
The copyright C (©) aligns with the G of HONG, and the F of G.M.F.G.I. aligns with the G of KONG.

Kader M1 1b:
The copyright C (©) aligns with the O of HONG, and the second G of G.M.F.G.I. aligns with the G of KONG.`
    );

    appendImageCard(
      "2. Kader M2",
      "/public/images/jawa_figure_kader_M2.png",
      `Kader M2 1a:
The right side of the copyright C (©) aligns with the H of HONG, and the 1 of 1977 aligns with the G of KONG.

Kader M2 1b:
The right side of the copyright C (©) aligns with the H of HONG, and the middle of the 9 and 7 of 1977 aligns with the G of KONG.`
    );

    appendImageCard(
      "3. Unitoy M3",
      "/public/images/jawa_figure_unitoy_M3.png",
      `Unitoy M3 1a:
The first G of G.M.F.G.I. aligns with the H of HONG, and the middle of the 77 from 1977 aligns with the G of KONG.

Unitoy M3 1b:
The first G of G.M.F.G.I. aligns with the H of HONG, and the middle of the 77 from 1977 aligns with the G of KONG.`
    );

    appendImageCard(
      "4. Unitoy / Lili Ledy M4",
      "/public/images/jawa_figure_unitoy_lili-ledy_M4.png",
      `Unitoy / Lili Ledy M4 1a:
The M of G.M.F.G.I. aligns with the H of HONG, and the middle of the second 7 from 1977 aligns with the G of KONG.

Unitoy / Lili Ledy M4 1b:
The M of G.M.F.G.I. aligns with the H of HONG, and the middle of the second 7 from 1977 aligns with the G of KONG.`
    );

    addBot(`Full Jawa guide on Variant Villain:
${VV_JAWA_URL}

Important:
DON’T RELY ON JUST THE COO TO IDENTIFY A FIGURE. Mould, paint colour, plastic colour and figure assembly traits are also needed to confirm your figure’s origins.`);
  }

  function choiceReply(choice) {
    const replies = {
      "kader-m1": `Closest match: Kader M1.

Now confirm with:
• bandolier shape and tone
• eye colour
• plastic colour
• cloak type, if present
• blaster mould, if present

This is a strong starting point, but do not rely on the leg marking alone.`,

      "kader-m2": `Closest match: Kader M2.

Now confirm with:
• bandolier shape and tone
• eye colour
• plastic colour
• cloak type, if present
• blaster mould, if present

This is a strong starting point, but do not rely on the leg marking alone.`,

      "unitoy-m3": `Closest match: Unitoy M3.

Now confirm with:
• bandolier shape and tone
• eye colour
• plastic colour
• cloak type, if present
• blaster mould, if present

This is a strong starting point, but do not rely on the leg marking alone.`,

      "unitoy-lili-ledy-m4": `Closest match: Unitoy / Lili Ledy M4.

Now confirm with:
• bandolier shape and tone
• eye colour
• plastic colour
• cloak type, if present
• blaster mould, if present

This is a strong starting point, but do not rely on the leg marking alone.`
    };

    return replies[choice] || null;
  }

  function unclearReply() {
    return `If it doesn't show either expected marking, be careful.

For original vintage Jawa figures, the normal left-leg markings are either:

• © G.M.F.G.I. 1977 with HONG KONG underneath
• or just © G.M.F.G.I. 1977 with no HONG KONG underneath

If yours appears to have neither, possible explanations include:
• very worn or faint markings
• poor lighting / difficult angle
• bootleg
• reproduction
• Retro Collection
• modern figure

For now, check under strong light and look again at the back of the left leg.`;
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

      state.step = "leg-marking";
      addBot(jawaLegQuestion(cape));
      return;
    }

    if (state.currentFigure === "jawa" && state.step === "leg-marking") {
      const answer = detectLegMarkingAnswer(t);

      if (answer === "no-coo") {
        state.step = "confirm-kader-no-coo";
        noCooKaderReply();
        return;
      }

      if (answer === "hong-kong") {
        state.step = "choose-reference";
        showHongKongReferenceImages();
        return;
      }

      if (answer === "unclear") {
        state.step = "unclear-marking";
        addBot(unclearReply());
        return;
      }

      addBot("Please reply with 1, 2, or 3.");
      return;
    }

    if (state.currentFigure === "jawa" && state.step === "choose-reference") {
      const choice = detectReferenceChoice(t);

      if (!choice) {
        addBot("Please reply with 1, 2, 3, or 4 for the closest reference image.");
        return;
      }

      state.step = "confirm-traits";
      addBot(choiceReply(choice));
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