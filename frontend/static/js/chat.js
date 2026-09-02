const chatEl = document.getElementById("chat");
const formEl = document.getElementById("chat-form");
const inputEl = document.getElementById("question-input");
const typingEl = document.getElementById("typing");
const errorEl = document.getElementById("error-banner");

function renderComparisonTable(comparison) {
  const table = document.createElement("table");
  table.className = "comparison-table";

  const header = document.createElement("tr");
  header.innerHTML = `<th></th><th>${comparison.item_a}</th><th>${comparison.item_b}</th>`;
  table.appendChild(header);

  comparison.rows.forEach(row => {
    const tr = document.createElement("tr");
    tr.innerHTML = `<td><strong>${row.label}</strong></td><td>${row.value_a}</td><td>${row.value_b}</td>`;
    table.appendChild(tr);
  });

  return table;
}

function addMessage(text, sender, extras = {}) {
  const msg = document.createElement("div");
  msg.className = `message ${sender}`;

  if (sender === "bot") {
    const body = document.createElement("div");
    body.innerHTML = marked.parse(text);
    msg.appendChild(body);

    if (extras.comparison) {
      msg.appendChild(renderComparisonTable(extras.comparison));
    }
  } else {
    msg.textContent = text;
  }

  if (extras.sources && extras.sources.length > 0) {
    const src = document.createElement("div");
    src.className = "sources";
    src.textContent = "Sources: " + extras.sources.map(s => `${s.source} (p.${s.page})`).join(", ");
    msg.appendChild(src);
  }

  chatEl.appendChild(msg);
  chatEl.scrollTop = chatEl.scrollHeight;
  return msg;
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
      body: JSON.stringify({ question: question }),
    });

    const data = await res.json();

    if (!res.ok) {
      throw new Error(data.error || "Something went wrong.");
    }

    addMessage(data.answer_markdown, "bot", {
      sources: data.sources || [],
      comparison: data.comparison || null,
    });
  } catch (err) {
    errorEl.textContent = err.message;
    errorEl.classList.remove("hidden");
  } finally {
    typingEl.classList.add("hidden");
    inputEl.disabled = false;
    inputEl.focus();
  }
});