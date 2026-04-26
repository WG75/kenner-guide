(function () {
  const logEl = document.getElementById("droidLog");
  const inputEl = document.getElementById("droidInput");
  const statusEl = document.getElementById("droidStatus");

  const state = { history: [] };

  function setStatus(text) {
    if (statusEl) statusEl.textContent = text || "";
  }

  function escapeHtml(text) {
    return String(text || "")
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;");
  }

  function linkify(text) {
    const escaped = escapeHtml(text);
    return escaped.replace(
      /(https?:\/\/[^\s<]+)/g,
      '<a href="$1" target="_blank" rel="noopener noreferrer">$1</a>'
    );
  }

  function formatText(text) {
    return linkify(text).replace(/\n/g, "<br>");
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
    if (!logEl || !imageUrl) return;
    const card = document.createElement("div");
    card.className = "vfcb-image-card";
    card.style.margin = "12px 0";
    card.style.padding = "12px";
    card.style.borderRadius = "12px";
    card.style.border = "1px solid rgba(255,255,255,0.15)";
    card.style.background = "rgba(255,255,255,0.04)";

    if (title) {
      const heading = document.createElement("div");
      heading.textContent = title;
      heading.style.fontWeight = "700";
      heading.style.marginBottom = "8px";
      card.appendChild(heading);
    }

    const img = document.createElement("img");
    img.src = imageUrl;
    img.alt = title || "VF-CB reference image";
    img.loading = "lazy";
    img.style.width = "100%";
    img.style.maxWidth = "100%";
    img.style.borderRadius = "10px";
    img.style.display = "block";
    img.style.marginBottom = caption ? "8px" : "0";
    card.appendChild(img);

    if (caption) {
      const note = document.createElement("div");
      note.innerHTML = formatText(caption);
      note.style.lineHeight = "1.45";
      card.appendChild(note);
    }

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

  async function askApi(message) {
    setStatus("Thinking...");
    const res = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message, history: state.history.slice(-30) })
    });
    const data = await res.json().catch(() => ({}));
    setStatus("");
    if (!res.ok) throw new Error(data?.error || "API error");
    return data;
  }

  async function processMessage(rawMessage) {
    const message = String(rawMessage || "").trim();
    if (!message) return;
    addUser(message);
    try {
      const data = await askApi(message);
      if (Array.isArray(data.images)) {
        data.images.forEach((img) => appendImageCard(img.title, img.url, img.caption));
      }
      addBot(data.reply || "I could not find a useful answer from the reference files.");
      if (data.debug && window.VFCB_DEBUG) console.log("VF-CB debug", data.debug);
    } catch (err) {
      console.error(err);
      setStatus("");
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