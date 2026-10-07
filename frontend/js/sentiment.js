const API_URL = "http://localhost:8000/predict";

const textInput = document.getElementById("input-text");
const analyzeBtn = document.getElementById("analyze-btn");
const resultCard = document.getElementById("result");

analyzeBtn.addEventListener("click", async () => {
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
      body: JSON.stringify({ text }),
    });

    if (!response.ok) {
      const errBody = await response.json().catch(() => ({}));
      throw new Error(errBody.detail || `Request failed (${response.status})`);
    }

    const data = await response.json();
    showResult(data);
  } catch (err) {
    showError(err.message || "Something went wrong. Is the Sentiment service running on port 8000?");
  } finally {
    setLoading(false);
  }
});

function setLoading(isLoading) {
  analyzeBtn.disabled = isLoading;
  analyzeBtn.innerHTML = isLoading ? '<span class="spinner"></span>Analyzing...' : "Analyze";
}

function showResult(data) {
  const labelClass = data.label === "POSITIVE" ? "label-positive" : "label-negative";
  resultCard.className = "result-card visible";
  resultCard.innerHTML = `
    <p><strong>Sentiment:</strong> <span class="${labelClass}">${data.label}</span></p>
    <p><strong>Confidence:</strong> ${(data.confidence * 100).toFixed(1)}%</p>
    <p style="color: var(--muted); font-size: 0.85rem;">Inference time: ${data.inference_time_ms}ms</p>
  `;
}

function showError(message) {
  resultCard.className = "result-card visible error";
  resultCard.innerHTML = `<p style="color: var(--error);">⚠️ ${message}</p>`;
}