const chatBox = document.querySelector("#vfcb-chat-box");
const input = document.querySelector("#vfcb-input");
const sendBtn = document.querySelector("#vfcb-send");

let history = [];

function addMessage(role, text) {
  const div = document.createElement("div");
  div.className = role === "user" ? "user-msg" : "bot-msg";
  div.innerText = text;
  chatBox.appendChild(div);
  chatBox.scrollTop = chatBox.scrollHeight;
}

async function sendMessage() {
  const message = input.value.trim();
  if (!message) return;

  addMessage("user", message);

  history.push({ role: "user", content: message });

  input.value = "";

  try {
    const res = await fetch("/api/chat", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        message,
        history,
      }),
    });

    const data = await res.json();

    if (!data.reply) {
      throw new Error("No reply");
    }

    addMessage("assistant", data.reply);

    history.push({
      role: "assistant",
      content: data.reply,
    });

  } catch (err) {
    console.error(err);

    addMessage(
      "assistant",
      "Something went wrong getting a response. Try again."
    );
  }
}

sendBtn.addEventListener("click", sendMessage);

input.addEventListener("keydown", (e) => {
  if (e.key === "Enter") {
    sendMessage();
  }
});
