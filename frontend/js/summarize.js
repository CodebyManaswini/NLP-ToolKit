const API_URL = `http://${window.location.hostname}:8002/summarize`;

const fileDrop = document.getElementById("file-drop");
const fileInput = document.getElementById("file-input");
const fileDropText = document.getElementById("file-drop-text");
const summarizeBtn = document.getElementById("summarize-btn");
const resultCard = document.getElementById("result");

let selectedFile = null;

fileDrop.addEventListener("click", () => fileInput.click());

fileInput.addEventListener("change", () => {
  if (fileInput.files.length > 0) {
    selectedFile = fileInput.files[0];
    fileDropText.textContent = `Selected: ${selectedFile.name}`;
    summarizeBtn.disabled = false;
  }
});

summarizeBtn.addEventListener("click", async () => {
  if (!selectedFile) return;

  setLoading(true);

  const formData = new FormData();
  formData.append("file", selectedFile);

  try {
    const response = await fetch(API_URL, {
      method: "POST",
      body: formData,
    });

    if (!response.ok) {
      const errBody = await response.json().catch(() => ({}));
      throw new Error(errBody.detail || `Request failed (${response.status})`);
    }

    const data = await response.json();
    showResult(data);
  } catch (err) {
    showError(err.message || "Something went wrong. Is the Summarization service running on port 8002?");
  } finally {
    setLoading(false);
  }
});

function setLoading(isLoading) {
  summarizeBtn.disabled = isLoading;
  summarizeBtn.innerHTML = isLoading ? '<span class="spinner"></span>Summarizing...' : "Summarize";
}

function showResult(data) {
  resultCard.className = "result-card visible";
  resultCard.innerHTML = `
    <p><strong>Summary:</strong></p>
    <p>${data.summary}</p>
    <p style="color: var(--muted); font-size: 0.85rem; margin-top: 16px;">
      ${data.original_word_count} words → ${data.summary_word_count} words
      (${data.chunk_count} chunk${data.chunk_count > 1 ? "s" : ""}, ${(data.processing_time_ms / 1000).toFixed(1)}s)
    </p>
  `;
}

function showError(message) {
  resultCard.className = "result-card visible error";
  resultCard.innerHTML = `<p style="color: var(--error);">⚠️ ${message}</p>`;
}