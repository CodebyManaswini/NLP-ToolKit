const API_URL = "http://localhost:8001/check";

const textInput = document.getElementById("input-text");
const checkBtn = document.getElementById("check-btn");
const resultCard = document.getElementById("result");

checkBtn.addEventListener("click", async () => {
  const text = textInput.value.trim();
  if (!text) {
    showError("Please enter some text first.");
    return;
  }

  setLoading(true);

  try {
    const response = await fetch(API_URL, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text, language: "en-US" }),
    });

    if (!response.ok) {
      const errBody = await response.json().catch(() => ({}));
      throw new Error(errBody.detail || `Request failed (${response.status})`);
    }

    const data = await response.json();
    showResult(data);
  } catch (err) {
    showError(err.message || "Something went wrong. Is the Grammar service running on port 8001?");
  } finally {
    setLoading(false);
  }
});

function setLoading(isLoading) {
  checkBtn.disabled = isLoading;
  checkBtn.innerHTML = isLoading ? '<span class="spinner"></span>Checking...' : "Check Grammar";
}

function showResult(data) {
  resultCard.className = "result-card visible";

  if (data.issue_count === 0) {
    resultCard.innerHTML = `<p style="color: var(--success);">✅ No issues found — looks good!</p>`;
    return;
  }

  let html = `<p><strong>${data.issue_count} issue(s) found:</strong></p>`;
  for (const issue of data.issues) {
    const replacementsText = issue.replacements.length
      ? `Suggestions: ${issue.replacements.join(", ")}`
      : "";
    html += `
      <div class="issue">
        <div class="category">${issue.category}</div>
        <p style="margin: 4px 0;">${issue.message}</p>
        <p style="color: var(--muted); font-size: 0.85rem; margin: 0;">${replacementsText}</p>
      </div>
    `;
  }
  resultCard.innerHTML = html;
}

function showError(message) {
  resultCard.className = "result-card visible error";
  resultCard.innerHTML = `<p style="color: var(--error);">⚠️ ${message}</p>`;
}