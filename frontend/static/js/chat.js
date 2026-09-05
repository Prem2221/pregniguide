const chatEl = document.getElementById("chat");
const formEl = document.getElementById("chat-form");
const inputEl = document.getElementById("question-input");
const typingEl = document.getElementById("typing");
const errorEl = document.getElementById("error-banner");
const languageSelect = document.getElementById("language-select");
const newChatBtn = document.getElementById("new-chat-btn");

let sessionId = null;

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

function renderFollowUps(questions) {
  const wrap = document.createElement("div");
  wrap.className = "follow-ups";

  questions.forEach(q => {
    const btn = document.createElement("button");
    btn.type = "button";
    btn.className = "follow-up-btn";
    btn.textContent = q;
    btn.addEventListener("click", () => {
      inputEl.value = q;
      formEl.requestSubmit();
    });
    wrap.appendChild(btn);
  });

  return wrap;
}

function addMessage(text, sender, extras = {}) {
  const msg = document.createElement("div");
  msg.className = `message ${sender}`;

  if (sender === "bot") {
    const body = document.createElement("div");
    body.className = "message-body";
    body.innerHTML = marked.parse(text);
    msg.appendChild(body);

    if (extras.comparison) {
      msg.appendChild(renderComparisonTable(extras.comparison));
    }
    if (extras.followUps && extras.followUps.length > 0) {
      msg.appendChild(renderFollowUps(extras.followUps));
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

  // Queue and typewriter state
  let displayedText = "";
  let pendingQueue = "";
  let typewriterTimer = null;

  function startTypewriter(bodyEl) {
    if (typewriterTimer) return;
    typewriterTimer = setInterval(() => {
      if (pendingQueue.length === 0) return;
      const takeChars = 3;
      displayedText += pendingQueue.slice(0, takeChars);
      pendingQueue = pendingQueue.slice(takeChars);
      bodyEl.innerHTML = marked.parse(displayedText);
      chatEl.scrollTop = chatEl.scrollHeight;
    }, 20);
  }

  function stopTypewriter() {
    if (typewriterTimer) {
      clearInterval(typewriterTimer);
      typewriterTimer = null;
    }
  }

  try {
    const botMsg = addMessage("", "bot");
    const bodyEl = botMsg.querySelector(".message-body"); // Direct reference to the rendered body

    const res = await fetch("/ask-stream", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        question: question,
        session_id: sessionId,
        language: languageSelect.value,
      }),
    });

    if (!res.ok) {
      let message = `Server error (${res.status}). Please try again.`;
      try {
        const errData = await res.json();
        if (errData.error) message = errData.error;
      } catch (_) {
        // Fallback to generic status message
      }
      throw new Error(message);
    }

    const reader = res.body.getReader();
    const decoder = new TextDecoder();
    let buffer = "";

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split("\n");
      buffer = lines.pop();

      for (const line of lines) {
        if (!line.trim()) continue;
        const parsed = JSON.parse(line);

        if (parsed.type === "chunk") {
          pendingQueue += parsed.text;
          startTypewriter(bodyEl);
        } else if (parsed.type === "final") {
          const data = parsed.data;

          // Wait for remaining characters in queue
          await new Promise(resolve => {
            const check = setInterval(() => {
              if (pendingQueue.length === 0) {
                clearInterval(check);
                resolve();
              }
            }, 20);
          });

          stopTypewriter();
          bodyEl.innerHTML = marked.parse(data.answer_markdown);

          if (data.comparison) {
            botMsg.appendChild(renderComparisonTable(data.comparison));
          }
          if (data.follow_up_questions && data.follow_up_questions.length > 0) {
            botMsg.appendChild(renderFollowUps(data.follow_up_questions));
          }
          if (data.sources && data.sources.length > 0) {
            const src = document.createElement("div");
            src.className = "sources";
            src.textContent = "Sources: " + data.sources.map(s => `${s.source} (p.${s.page})`).join(", ");
            botMsg.appendChild(src);
          }

          sessionId = data.session_id || sessionId;
          languageSelect.disabled = true;
        } else if (parsed.type === "error") {
          throw new Error(parsed.message);
        }
      }
    }
  } catch (err) {
    stopTypewriter();
    errorEl.textContent = err.message;
    errorEl.classList.remove("hidden");
  } finally {
    typingEl.classList.add("hidden");
    inputEl.disabled = false;
    inputEl.focus();
  }
});

newChatBtn.addEventListener("click", () => {
  sessionId = null;
  chatEl.innerHTML = "";
  languageSelect.disabled = false;
  errorEl.classList.add("hidden");
  inputEl.value = "";
  inputEl.focus();
});