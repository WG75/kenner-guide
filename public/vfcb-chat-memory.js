const chatBox = document.querySelector("#vfcb-chat-box");
const input = document.querySelector("#vfcb-input");
const sendBtn = document.querySelector("#vfcb-send");

let history = [];

function addMessage(role, text, imageUrl = null) {
  const div = document.createElement("div");
  div.className = role === "user" ? "user-msg" : "bot-msg";
  div.innerText = text;

  chatBox.appendChild(div);

  // Add image if provided
  if (imageUrl) {
    const img = document.createElement("img");
    img.src = imageUrl;
    img.style.maxWidth = "100%";
    img.style.marginTop = "8px";
    img.style.borderRadius = "6px";
    chatBox.appendChild(img);
  }

  chatBox.scrollTop = chatBox.scrollHeight;
}

function normalise(text) {
  return (text || "").toLowerCase().trim();
}

function isNoCOO(text) {
  return (
    text.includes("no coo") ||
    text.includes("no country") ||
    text.includes("nothing") ||
    text.includes("just 1977") ||
    text.includes("only copyright") ||
    text.includes("no marking")
  );
}

function sendMessage() {
  const message = input.value.trim();
  if (!message) return;

  addMessage("user", message);
  input.value = "";

  const lower = normalise(message);

  // STEP 1: Jawa detection
  if (lower.includes("jawa")) {
    addMessage(
      "assistant",
      `Yes I can do that — let's start with the cape.

Which of these does your Jawa have?

1. Vinyl cape - smooth plastic
2. Cloth cloak - fabric
3. Or neither. Just a naked figure

Reply with 1, 2 or 3.`
    );
    return;
  }

  // STEP 2: Cape missing
  if (lower === "3" || lower.includes("missing")) {
    addMessage(
      "assistant",
      `Right — so your Jawa is missing its cape, what collectors would usually call a naked figure.

Next step:
Check the Country of Origin (COO) markings on the legs.

Original vintage figures usually have:
• Hong Kong
• China
• Taiwan
• or no COO marking

What does your figure say?`
    );
    return;
  }

  // STEP 3: NO COO logic (THIS is the fix)
  if (isNoCOO(lower)) {
    addMessage(
      "assistant",
      `Right — if there’s no country marking and only a copyright line, you’re into Kader China territory.

These typically read:
© G.M.F.G.I. 1977

That stands for General Mills Fun Group Incorporated.

This is what collectors call a No COO Jawa, produced in China by Kader.

This variant originally came with:
• Smooth cloth cloak
• M2 Kader Jawa blaster (short bump)

Compare your leg marking to this reference:`,
      "/images/jawa_figure_kader_china_M2.png"
    );

    addMessage(
      "assistant",
      `View the full guide on Variant Villain:
https://www.variantvillain.com/characters/jawa/`
    );

    addMessage(
      "assistant",
      `Next checks:
• bandolier tone
• eye colour
• cloak type (if present)

There are two main No COO variants, mainly distinguished by the size of the copyright text.`
    );

    return;
  }

  // fallback
  addMessage(
    "assistant",
    "Tell me what the leg marking says — for example Hong Kong, Taiwan, or no COO."
  );
}

sendBtn.addEventListener("click", sendMessage);

input.addEventListener("keydown", (e) => {
  if (e.key === "Enter") {
    sendMessage();
  }
});