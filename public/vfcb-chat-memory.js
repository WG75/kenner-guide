const chatBox = document.querySelector("#vfcb-chat-box");
const input = document.querySelector("#vfcb-input");
const sendBtn = document.querySelector("#vfcb-send");

let history = [];
let context = {
  currentFigure: null,
  step: null
};

function addMessage(role, text) {
  const div = document.createElement("div");
  div.className = role === "user" ? "user-msg" : "bot-msg";
  div.innerText = text;
  chatBox.appendChild(div);
  chatBox.scrollTop = chatBox.scrollHeight;
}

function detectJawaStart(message) {
  const msg = message.toLowerCase();
  return msg.includes("jawa");
}

function detectCapeAnswer(message) {
  const msg = message.toLowerCase();

  if (msg === "1" || msg.includes("vinyl")) return "vinyl";
  if (msg === "2" || msg.includes("cloth")) return "cloth";
  if (msg === "3" || msg.includes("no cape") || msg.includes("naked")) return "none";

  return null;
}

async function sendMessage() {
  const message = input.value.trim();
  if (!message) return;

  addMessage("user", message);
  input.value = "";

  // ---------- LOCAL LOGIC FIRST (IMPORTANT) ----------

  // Start Jawa flow
  if (!context.currentFigure && detectJawaStart(message)) {
    context.currentFigure = "jawa";
    context.step = "cape";

    addMessage("assistant",
`Yes I can do that — let's start with the cape.

Which of these does your Jawa have?

1. Vinyl cape - smooth plastic  
2. Cloth cloak - fabric  
3. Or neither. Just a naked figure  

Just tell me: vinyl, cloth, or missing cloak.  
Or reply with 1, 2 or 3.`);

    return;
  }

  // Handle cape step
  if (context.currentFigure === "jawa" && context.step === "cape") {
    const cape = detectCapeAnswer(message);

    if (!cape) {
      addMessage("assistant", "Just reply with 1, 2 or 3 — or vinyl, cloth, or no cape.");
      return;
    }

    context.step = "coo";

    if (cape === "none") {
      addMessage("assistant",
`Good — so we’re dealing with a Jawa missing its cape.

Next step: check the leg markings.

Look closely at the back of the legs. Can you see:

• "Hong Kong"
• "Taiwan"
• or just a single line like "© G.M.F.G.I. 1977"?

Tell me exactly what you can read.`);
    }

    if (cape === "cloth") {
      addMessage("assistant",
`Good — cloth cloak.

Next step: check the COO marking on the legs.

Also note:
• hood size and shape
• stitching style

What does the COO say?`);
    }

    if (cape === "vinyl") {
      addMessage("assistant",
`Vinyl cape — early production.

Now we need to confirm COO and figure traits.

What does the leg marking say?`);
    }

    return;
  }

  // Handle COO step (basic detection)
  if (context.currentFigure === "jawa" && context.step === "coo") {
    const msg = message.toLowerCase();

    if (msg.includes("1977") && !msg.includes("hong kong") && !msg.includes("taiwan")) {
      addMessage("assistant",
`If you can’t see "Hong Kong" or "Taiwan", and it only reads:

"© G.M.F.G.I. 1977"

Then you’re looking at a Kader (China) no COO Jawa.

That stands for General Mills Fun Group Incorporated.

Typical traits:
• Dark brown rectangular bandolier  
• Round yellow eyes  
• Smooth cloth cloak (if present)  

Paired with:
• M2 Jawa blaster (short rear bump)

There are two variants here — mainly differing in the size of the copyright text.`);
      return;
    }

    addMessage("assistant",
`Good — that helps.

To confirm fully, I’d also want:
• bandolier colour/shape
• eye colour
• cloak (if present)
• blaster type

Send what you can see and I’ll narrow it further.`);
    return;
  }

  // ---------- FALLBACK TO API ----------

  try {
    history.push({ role: "user", content: message });

    const res = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ messages: history })
    });

    const data = await res.json();

    if (!data.reply) throw new Error("No reply");

    addMessage("assistant", data.reply);

    history.push({
      role: "assistant",
      content: data.reply
    });

  } catch (err) {
    console.error(err);
    addMessage("assistant", "Something went wrong getting a response.");
  }
}

sendBtn.addEventListener("click", sendMessage);

input.addEventListener("keydown", (e) => {
  if (e.key === "Enter") sendMessage();
});
