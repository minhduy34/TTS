// ai/src/frontend/app.js
const SESSION_ID = "session-" + Math.random().toString(36).slice(2);
const chat     = document.getElementById("chat");
const input    = document.getElementById("input");
const sendBtn  = document.getElementById("sendBtn");
const statusBar = document.getElementById("statusBar");

function sendMessage() {
  const text = input.value.trim();
  if (!text) return;
  addBubble("user", text);
  input.value = "";
  autoResize();
  setLoading(true);
  streamResponse(text);
}

function streamResponse(message) {
  const url = `/chat/stream?session_id=${encodeURIComponent(SESSION_ID)}&message=${encodeURIComponent(message)}`;
  const es = new EventSource(url);

  es.addEventListener("status", (e) => {
    const data = JSON.parse(e.data);
    showStatus(data.message);
  });

  es.addEventListener("done", (e) => {
    const data = JSON.parse(e.data);
    hideStatus();
    addBubble("agent", data.reply, data.reasoning);
    setLoading(false);
    es.close();
  });

  es.addEventListener("error", (e) => {
    hideStatus();
    let msg = "😅 Mình bị lỗi rồi bạn ơi, thử lại nhé!";
    try { msg = JSON.parse(e.data).message; } catch(_) {}
    addBubble("agent", msg);
    setLoading(false);
    es.close();
  });

  es.onerror = () => {
    if (es.readyState === EventSource.CLOSED) return;
    hideStatus();
    addBubble("agent", "😅 Mất kết nối rồi bạn ơi, thử lại nhé!");
    setLoading(false);
    es.close();
  };
}

function addBubble(role, text, reasoning) {
  const wrap = document.createElement("div");
  wrap.className = `bubble ${role}`;

  const avatar = document.createElement("span");
  avatar.className = "avatar";
  avatar.textContent = role === "user" ? "🎓" : "🤖";

  const content = document.createElement("div");
  content.className = "bubble-content-wrap";

  const body = document.createElement("div");
  body.className = "bubble-content";
  body.textContent = text;
  content.appendChild(body);

  if (reasoning) {
    const toggle = document.createElement("div");
    toggle.className = "reasoning-toggle";
    toggle.textContent = "🔍 Xem cách mình nghĩ";
    const box = document.createElement("div");
    box.className = "reasoning-content";
    box.textContent = reasoning;
    box.hidden = true;
    toggle.onclick = () => {
      box.hidden = !box.hidden;
      toggle.textContent = box.hidden ? "🔍 Xem cách mình nghĩ" : "🔼 Ẩn đi";
    };
    content.appendChild(toggle);
    content.appendChild(box);
  }

  wrap.appendChild(avatar);
  wrap.appendChild(content);
  chat.appendChild(wrap);
  chat.scrollTop = chat.scrollHeight;
}

function showStatus(msg) {
  statusBar.textContent = msg;
  statusBar.hidden = false;
  chat.scrollTop = chat.scrollHeight;
}

function hideStatus() {
  statusBar.hidden = true;
  statusBar.textContent = "";
}

function setLoading(loading) {
  sendBtn.disabled = loading;
  input.disabled   = loading;
}

function autoResize() {
  input.style.height = "auto";
  input.style.height = Math.min(input.scrollHeight, 120) + "px";
}

input.addEventListener("input", autoResize);
input.addEventListener("keydown", (e) => {
  if (e.key === "Enter" && !e.shiftKey) {
    e.preventDefault();
    sendMessage();
  }
});
