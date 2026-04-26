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

  function appendBotHtml(html, historyText) {
    if (!logEl) return;

    const wrap = document.createElement("div");
    wrap.className = "vfcb-msg vfcb-assistant";
    wrap.style.margin = "10px 0";
    wrap.style.padding = "12px 14px";
    wrap.style.borderRadius = "12px";
    wrap.style.lineHeight = "1.5";
    wrap.innerHTML = html;

    logEl.appendChild(wrap);
    logEl.scrollTop = logEl.scrollHeight;

    state.history.push({
      role: "assistant",
      content: historyText || wrap.textContent || ""
    });
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
    return normalise(text).includes("jawa");
  }

  function detectCapeAnswer(text) {
    const t = normalise(text);

    if (t === "1" || t.includes("vinyl")) return "vinyl";
    if (t === "2" || t.includes("cloth") || t.includes("fabric") || t.includes("cloak")) return "cloth";

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

    if (
      t === "1" ||
      t.includes("hong kong") ||
      t.includes("says hong") ||
      t.includes("has hong") ||
      t.includes("it says hong") ||
      t.includes("yes says hong")
    ) {
      return "hong-kong";
    }

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

  function detectYesNo(text) {
    const t = normalise(text);

    if (
      t === "1" ||
      t === "yes" ||
      t === "y" ||
      t.includes("yes") ||
      t.includes("blaster") ||
      t.includes("weapon")
    ) {
      return "yes";
    }

    if (t === "2" || t === "no" || t === "n" || t.includes("no") || t.includes("done")) {
      return "no";
    }

    return null;
  }

  function referenceLabel(choice) {
    const labels = {
      "kader-m1": "Kader M1",
      "kader-m2": "Kader M2",
      "unitoy-m3": "Unitoy M3",
      "unitoy-lili-ledy-m4": "Unitoy / Lili Ledy M4"
    };

    return labels[choice] || "that Jawa";
  }

  function referenceUrl(choice) {
    const links = {
      "kader-m1": "https://www.variantvillain.com/characters/sw/jawa/#f1",
      "kader-m2": "https://www.variantvillain.com/characters/sw/jawa/#f2",
      "unitoy-m3": "https://www.variantvillain.com/characters/sw/jawa/#f3",
      "unitoy-lili-ledy-m4": "https://www.variantvillain.com/characters/sw/jawa/#f3"
    };

    return links[choice] || VV_JAWA_URL;
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
Check the Country of Origin markings on the legs.

Reply with:

1 for Hong Kong
2 if it doesn't show Hong Kong
3 if you can't tell / it doesn't appear to have either`;
    }

    if (capeType === "cloth") {
      return `Good — so we're dealing with a cloth cloak Jawa.

There are 5 known cloth cloak types. This app can help you get started, but for cloak confirmation the best visual reference is the Variant Villain cloak guide:

${VV_JAWA_CLOAK_URL}

Now let's identify the figure itself.

Next step:
Check the Country of Origin markings on the legs.

Reply with:

1 for Hong Kong
2 if it doesn't show Hong Kong
3 if you can't tell / it doesn't appear to have either`;
    }

    if (capeType === "vinyl") {
      return `Ok — let's treat this as a potential vinyl cape Jawa, not confirmed yet.

Original vinyl cape Jawas are very valuable, so unfortunately there are many fakes and cut-down Ben Kenobi capes around.

This app is a useful starting point, but don't rely on it alone. For anything valuable, get confirmation from experienced collector groups as well.

First, compare your cape shape, surface texture and colour against this reference:`;
    }

    return "";
  }

  function showVinylCapeReference() {
    appendImageCard(
      "Jawa Vinyl Cape Authentication Reference",
      "/public/images/jawa-vinyl-cape-01.png",
      `Compare:
• cape shape
• surface texture on both sides
• colour compared with an original Ben cape
• signs of a cut-down cape

A cut-down Ben cape is usually noticeably darker and the shape will not match correctly.`
    );

    appendBotHtml(
      `For more detailed information and reference photos, please check:<br>
<a href="${VV_JAWA_VINYL_CAPE_URL}" target="_blank" rel="noopener noreferrer">${VV_JAWA_VINYL_CAPE_URL}</a>`,
      `For more detailed information and reference photos, please check:
${VV_JAWA_VINYL_CAPE_URL}`
    );

    addBot(`Next, let's identify the figure itself.

Check the Country of Origin markings on the legs.

Reply with:

1 for Hong Kong
2 if it doesn't show Hong Kong
3 if you can't tell / it doesn't appear to have either`);
  }

  function noCooKaderReply() {
    addBot(`That points to the Kader China M2 No COO Jawa.

It should show just:
© G.M.F.G.I. 1977

No HONG KONG underneath.

Compare your leg marking with this reference:`);

    appendImageCard(
      "Kader China M2 No COO",
      "/public/images/jawa_figure_kader_china_M2.png",
      `Kader China M2 2a and M2 2b:
Only © G.M.F.G.I. 1977. No HONG KONG marking.

Notice the size difference between 2a and 2b, and how the 2a version's text aligns with the fold.`
    );

    appendBotHtml(
      `This figure variant is associated with Kader M2.<br><br>
For a more detailed look at the Kader M2 Jawa, please visit:<br>
<a href="https://www.variantvillain.com/characters/sw/jawa/#f2" target="_blank" rel="noopener noreferrer">https://www.variantvillain.com/characters/sw/jawa/#f2</a><br><br>
Do you also want help checking the Jawa blaster?<br><br>
1. Yes, help me identify the blaster<br>
2. No, I’m done for now`,
      `This figure variant is associated with Kader M2.

For a more detailed look at the Kader M2 Jawa, please visit:
https://www.variantvillain.com/characters/sw/jawa/#f2

Do you also want help checking the Jawa blaster?

1. Yes, help me identify the blaster
2. No, I’m done for now`
    );

    state.step = "jawa-blaster-choice";
  }

  function showHongKongReferenceImages() {
    addBot(`Great! Now let's check which figure variant you have.

Compare your left-leg marking with these reference images and choose the closest match.

Use the following images to compare your leg marks. On the images, look at the parts indicated in green.`);

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

    appendBotHtml(
      `Full Jawa guide on Variant Villain:<br>
<a href="${VV_JAWA_URL}" target="_blank" rel="noopener noreferrer">${VV_JAWA_URL}</a><br><br>
If you can match your figure to one of the above reference images, please reply with:<br><br>
1 for Kader M1<br>
2 for Kader M2<br>
3 for Unitoy M3<br>
4 for Unitoy / Lili Ledy M4`,
      `Full Jawa guide on Variant Villain:
${VV_JAWA_URL}

If you can match your figure to one of the above reference images, please reply with:

1 for Kader M1
2 for Kader M2
3 for Unitoy M3
4 for Unitoy / Lili Ledy M4`
    );
  }

  function choiceReply(choice) {
    const label = referenceLabel(choice);
    const url = referenceUrl(choice);

    appendBotHtml(
      `Closest match: ${label}.<br><br>
For a more detailed look at the ${label} Jawas, please visit:<br>
<a href="${url}" target="_blank" rel="noopener noreferrer">${url}</a><br><br>
Do you also want help checking the Jawa blaster?<br><br>
1. Yes, help me identify the blaster<br>
2. No, I’m done for now`,
      `Closest match: ${label}.

For a more detailed look at the ${label} Jawas, please visit:
${url}

Do you also want help checking the Jawa blaster?

1. Yes, help me identify the blaster
2. No, I’m done for now`
    );
  }

  function showBlasterReference() {
    addBot(`Ok — compare your blaster with this Jawa blaster reference image.`);

    appendImageCard(
      "Jawa Blaster Reference",
      "https://www.variantvillain.com/wp-content/uploads/2021/12/JawaBlaster_000.jpg",
      `Check:
• mould shape
• rear bump length
• plastic colour
• detail sharpness
• whether it looks like original vintage plastic or a modern repro`
    );

    appendBotHtml(
      `First quick test if you are unsure: try the float test.<br><br>
Older and cheaper reproductions usually sink in water. Original vintage blasters should float, even after being pushed under.<br><br>
Important: some newer reproductions are designed to deceive collectors and can also float. So if it floats, that does not prove it is original. You still need to compare the exact mould details.<br><br>
Most original Jawa blasters are shades of dark blue. Grey examples need extra caution because common grey reproductions exist.<br><br>
For more details and reference images, visit:<br>
<a href="${VV_JAWA_BLASTER_URL}" target="_blank" rel="noopener noreferrer">${VV_JAWA_BLASTER_URL}</a><br><br>
Ask me what colour yours is, whether it floats, or what rear bump it has, and I’ll guide you.`,
      `First quick test if you are unsure: try the float test.

Older and cheaper reproductions usually sink in water. Original vintage blasters should float, even after being pushed under.

Important: some newer reproductions are designed to deceive collectors and can also float. So if it floats, that does not prove it is original. You still need to compare the exact mould details.

Most original Jawa blasters are shades of dark blue. Grey examples need extra caution because common grey reproductions exist.

For more details and reference images, visit:
${VV_JAWA_BLASTER_URL}

Ask me what colour yours is, whether it floats, or what rear bump it has, and I’ll guide you.`
    );

    state.currentFigure = "jawa";
    state.step = "jawa-blaster-question";
  }

  function jawaBlasterQuestionReply(message) {
    const t = normalise(message);

    if (t.includes("grey") || t.includes("gray") || t.includes("silver")) {
      appendBotHtml(
        `Be careful here.<br><br>
Most original Jawa blasters are shades of dark blue. There is a very rare silver version associated with the Brazilian Glasslite figure, but grey Jawa blasters are also commonly seen as reproductions.<br><br>
First check:<br>
• Does it float in water?<br>
• If it sinks, treat it as a reproduction.<br>
• If it floats, that still does not prove it is original, because newer reproductions may also float.<br><br>
Next compare it closely against the known Variant Villain examples:<br>
<a href="${VV_JAWA_BLASTER_URL}" target="_blank" rel="noopener noreferrer">${VV_JAWA_BLASTER_URL}</a><br><br>
I would not call a grey Jawa blaster original without very careful comparison, especially to rule out a common grey repro.`,
        `Be careful here.

Most original Jawa blasters are shades of dark blue. There is a very rare silver version associated with the Brazilian Glasslite figure, but grey Jawa blasters are also commonly seen as reproductions.

First check:
• Does it float in water?
• If it sinks, treat it as a reproduction.
• If it floats, that still does not prove it is original, because newer reproductions may also float.

Next compare it closely against the known Variant Villain examples:
${VV_JAWA_BLASTER_URL}

I would not call a grey Jawa blaster original without very careful comparison, especially to rule out a common grey repro.`
      );
      return;
    }

    if (t.includes("float") || t.includes("floats") || t.includes("sink") || t.includes("sinks")) {
      appendBotHtml(
        `The float test is a useful first filter.<br><br>
• If the blaster sinks, treat it as a reproduction.<br>
• If it floats, it may be original, but this is not proof.<br>
• Newer reproductions can be made to float, so you still need to compare mould shape, rear bump, detail sharpness and plastic colour.<br><br>
Use the Variant Villain reference images here:<br>
<a href="${VV_JAWA_BLASTER_URL}" target="_blank" rel="noopener noreferrer">${VV_JAWA_BLASTER_URL}</a>`,
        `The float test is a useful first filter.

• If the blaster sinks, treat it as a reproduction.
• If it floats, it may be original, but this is not proof.
• Newer reproductions can be made to float, so you still need to compare mould shape, rear bump, detail sharpness and plastic colour.

Use the Variant Villain reference images here:
${VV_JAWA_BLASTER_URL}`
      );
      return;
    }

    appendBotHtml(
      `For Jawa blasters, start with the float test if you are unsure.<br><br>
Then compare:<br>
• mould shape<br>
• rear bump length<br>
• plastic colour, usually dark blue tones for most originals<br>
• sharpness of the mould detail<br>
• whether it matches a known original example exactly<br><br>
Variant Villain reference page:<br>
<a href="${VV_JAWA_BLASTER_URL}" target="_blank" rel="noopener noreferrer">${VV_JAWA_BLASTER_URL}</a>`,
      `For Jawa blasters, start with the float test if you are unsure.

Then compare:
• mould shape
• rear bump length
• plastic colour, usually dark blue tones for most originals
• sharpness of the mould detail
• whether it matches a known original example exactly

Variant Villain reference page:
${VV_JAWA_BLASTER_URL}`
    );
  }

  function unclearReply() {
    return `If it doesn't show either expected marking, be careful.

For original vintage Jawa figures, the normal left-leg markings are either:

• © G.M.F.G.I. 1977 with HONG KONG underneath
• or just © G.M.F.G.I. 1977 with no HONG KONG underneath

If yours appears to have neither, possible explanations include:

• Very damaged, worn or faint markings
• Poor lighting / difficult angle
• Bootleg
• Reproduction
• Retro Collection
• Modern figure

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

    if (!state.currentFigure && isJawaBlasterStart(t)) {
      showBlasterReference();
      return;
    }

    if (!state.currentFigure && isJawaStart(t)) {
      state.currentFigure = "jawa";
      state.step = "cape";
      state.selectedReference = null;
      state.capeType = null;
      addBot(jawaOpening());
      return;
    }

    if (state.currentFigure === "jawa" && state.step === "cape") {
      const cape = detectCapeAnswer(t);

      if (!cape) {
        addBot("Just reply with 1, 2 or 3 — or vinyl, cloth, or missing cloak.");
        return;
      }

      state.capeType = cape;

      if (cape === "vinyl") {
        state.step = "leg-marking";
        addBot(jawaLegQuestion(cape));
        showVinylCapeReference();
        return;
      }

      state.step = "leg-marking";
      addBot(jawaLegQuestion(cape));
      return;
    }

    if (
      state.currentFigure === "jawa" &&
      (state.step === "leg-marking" || state.step === "unclear-marking")
    ) {
      const answer = detectLegMarkingAnswer(t);

      if (answer === "no-coo") {
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

      state.selectedReference = choice;
      choiceReply(choice);
      state.step = "jawa-blaster-choice";
      return;
    }

    if (state.currentFigure === "jawa" && state.step === "jawa-blaster-choice") {
      const answer = detectYesNo(t);

      if (answer === "yes") {
        showBlasterReference();
        return;
      }

      if (answer === "no") {
        addBot("No problem. Is there anything else I can help you with?");
        state.step = null;
        state.currentFigure = null;
        return;
      }

      addBot("Please reply with 1 for yes, or 2 for no.");
      return;
    }

    if (state.currentFigure === "jawa" && state.step === "jawa-blaster-question") {
      jawaBlasterQuestionReply(message);
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