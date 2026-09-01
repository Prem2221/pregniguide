const chatEl = document.getElementById("chat");
const formEl = document.getElementById("chat-form");
const inputEl = document.getElementById("question-input");
const typingEl = document.getElementById("typing");
const errorEl = document.getElementById("error-banner");

function addMessage(text, sender, sources = []) {
  const msg = document.createElement("div");
  msg.className = `message ${sender}`;
  msg.textContent = text;

  if (sources.length > 0) {
    const src = document.createElement("div");
    src.className = "sources";
    src.textContent = "Sources: " + sources.map(s => `${s.source} (p.${s.page})`).join(", ");
    msg.appendChild(src);
  }

  chatEl.appendChild(msg);
  chatEl.scrollTop = chatEl.scrollHeight;
}

formEl.addEventListener("submit", async (e) => {
  e.preventDefault();
  const question = inputEl.value.trim();
  if (!question) return;

  errorEl.classList.add("hidden");
  addMessage(question, "user");
  inputEl.value = "";
  inputEl.disabled = true;
  typingEl.classList.remove("hidden");

  try {
    const res = await fetch("/ask", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question }),
    });

    const data = await res.json();

    if (!res.ok) {
      throw new Error(data.error || "Something went wrong.");
    }

    addMessage(data.answer, "bot", data.sources || []);
  } catch (err) {
    errorEl.textContent = err.message;
    errorEl.classList.remove("hidden");
  } finally {
    typingEl.classList.add("hidden");
    inputEl.disabled = false;
    inputEl.focus();
  }
});