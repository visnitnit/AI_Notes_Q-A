document.addEventListener("DOMContentLoaded", () => {
  const fileInput = document.getElementById("pdf_file");
  const fileName = document.getElementById("file-name");
  if (fileInput && fileName) {
    fileInput.addEventListener("change", () => {
      fileName.textContent = fileInput.files.length ? fileInput.files[0].name : "No file selected";
    });
  }

  const form = document.getElementById("question-form");
  if (!form) return;
  const input = document.getElementById("question-input");
  const log = document.getElementById("chat-log");
  const noteId = log.dataset.noteId;
  const button = form.querySelector("button");

  function addMessage(role, title, text, sources = []) {
    const wrapper = document.createElement("div");
    wrapper.className = `chat-message ${role}`;
    const heading = document.createElement("strong");
    heading.textContent = title;
    const paragraph = document.createElement("p");
    paragraph.textContent = text;
    wrapper.append(heading, paragraph);
    if (sources.length) {
      const sourceBox = document.createElement("div");
      sourceBox.className = "sources";
      const sourceTitle = document.createElement("strong");
      sourceTitle.textContent = "Sources in your PDF";
      sourceBox.appendChild(sourceTitle);
      sources.forEach(source => {
        const item = document.createElement("p");
        item.textContent = `Page ${source.page}: ${source.excerpt}`;
        sourceBox.appendChild(item);
      });
      wrapper.appendChild(sourceBox);
    }
    log.appendChild(wrapper);
    log.scrollTop = log.scrollHeight;
  }

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    const question = input.value.trim();
    if (!question) return;
    addMessage("user", "You", question);
    input.value = "";
    button.disabled = true;
    button.textContent = "Searching…";
    try {
      const response = await fetch(`/api/notes/${noteId}/ask`, {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({question})
      });
      const result = await response.json();
      if (!response.ok) throw new Error(result.error || "Could not get an answer.");
      addMessage("assistant", `NoteWise AI · ${result.confidence} confidence`, result.answer, result.sources);
    } catch (error) {
      addMessage("assistant", "NoteWise AI", error.message || "Something went wrong. Please try again.");
    } finally {
      button.disabled = false;
      button.textContent = "Ask question ↑";
      input.focus();
    }
  });
});
