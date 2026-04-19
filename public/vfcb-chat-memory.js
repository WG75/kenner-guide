/*
  VF-CB conversation memory helper
  --------------------------------
  1. Include this file on the page that hosts your chat UI.
  2. Wire sendVFChat(message) into your existing chat submit button.
  3. It stores the last 12 turns in localStorage and sends them to /api/chat.
*/

const VF_CB_STORAGE_KEY = "vfcb_chat_history_v1";

function vfcbLoadHistory() {
  try {
    const raw = localStorage.getItem(VF_CB_STORAGE_KEY);
    if (!raw) return [];
    const parsed = JSON.parse(raw);
    if (!Array.isArray(parsed)) return [];
    return parsed.filter(m => m && typeof m.content === "string" && (m.role === "user" || m.role === "assistant"));
  } catch {
    return [];
  }
}

function vfcbSaveHistory(history) {
  localStorage.setItem(VF_CB_STORAGE_KEY, JSON.stringify(history.slice(-12)));
}

function vfcbClearHistory() {
  localStorage.removeItem(VF_CB_STORAGE_KEY);
}

async function sendVFChat(message) {
  const history = vfcbLoadHistory();

  const response = await fetch("/api/chat", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      message,
      history,
    }),
  });

  const data = await response.json();

  if (!response.ok) {
    throw new Error(data?.error || "Chat request failed");
  }

  const updatedHistory = [
    ...history,
    { role: "user", content: message },
    { role: "assistant", content: data.reply || "" },
  ].slice(-12);

  vfcbSaveHistory(updatedHistory);

  return data;
}

// Optional helper for debugging in browser console
window.VFCB = {
  sendVFChat,
  vfcbLoadHistory,
  vfcbSaveHistory,
  vfcbClearHistory,
};
