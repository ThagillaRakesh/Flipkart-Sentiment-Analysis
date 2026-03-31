"use strict";

// API endpoint — change to your deployed Render URL when in production
// e.g. "https://opinion-miner.onrender.com"
const API = "http://localhost:5000";

// ── Helpers ──────────────────────────────────────────────────────────────────

function badge(label) {
  return `<span class="badge badge-${label.toLowerCase()}">${label}</span>`;
}

function verdictEmoji(label) {
  return label === "Positive" ? "😊" : label === "Negative" ? "😞" : "😐";
}

function fmt(n) {
  return typeof n === "number" ? n.toFixed(3) : "—";
}

// ── On load: detect current tab URL ──────────────────────────────────────────

const urlDisplay  = document.getElementById("url-display");
const urlBtn      = document.getElementById("url-btn");
const notFlipkart = document.getElementById("not-flipkart");

let currentUrl = "";

chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
  const tab = tabs[0];
  if (!tab || !tab.url) return;
  currentUrl = tab.url;

  if (currentUrl.includes("flipkart.com")) {
    urlDisplay.textContent = currentUrl;
    urlDisplay.title = currentUrl;
    urlBtn.disabled = false;
    notFlipkart.style.display = "none";
  } else {
    urlDisplay.textContent = "Not a Flipkart page";
    notFlipkart.style.display = "block";
    urlBtn.disabled = true;
  }
});

// ── Text analysis ─────────────────────────────────────────────────────────────

document.getElementById("text-btn").addEventListener("click", async () => {
  const text = document.getElementById("text-input").value.trim();
  if (!text) return;

  const btn = document.getElementById("text-btn");
  const resultEl = document.getElementById("text-result");
  btn.disabled = true;
  btn.textContent = "Analyzing…";
  resultEl.style.display = "none";

  try {
    const res  = await fetch(`${API}/analyze`, {
      method:  "POST",
      headers: { "Content-Type": "application/json" },
      body:    JSON.stringify({ text }),
    });
    const data = await res.json();

    if (data.error) {
      resultEl.innerHTML = `<div class="error-box">${data.error}</div>`;
    } else {
      const s = data.scores;
      resultEl.innerHTML = `
        <div class="verdict ${data.label}">
          <div class="icon">${data.emoji || verdictEmoji(data.label)}</div>
          <div>
            <strong>Sentiment: ${data.label}</strong>
            <p>Compound: ${fmt(s.compound)} &nbsp;|&nbsp;
               Pos: ${fmt(s.pos)} &nbsp;|&nbsp;
               Neu: ${fmt(s.neu)} &nbsp;|&nbsp;
               Neg: ${fmt(s.neg)}</p>
          </div>
        </div>`;
    }
  } catch (err) {
    resultEl.innerHTML = `<div class="error-box">Cannot reach Opinion Miner server.<br>
      Make sure Flask is running on localhost:5000.</div>`;
  } finally {
    btn.disabled = false;
    btn.textContent = "Analyze Sentiment";
    resultEl.style.display = "block";
  }
});

// ── URL (Flipkart) analysis ───────────────────────────────────────────────────

urlBtn.addEventListener("click", async () => {
  if (!currentUrl) return;

  urlBtn.disabled = true;
  urlBtn.textContent = "Scraping…";
  document.getElementById("url-spinner").style.display = "flex";
  const resultEl = document.getElementById("url-result");
  resultEl.style.display = "none";

  try {
    const res  = await fetch(`${API}/analyze-url`, {
      method:  "POST",
      headers: { "Content-Type": "application/json" },
      body:    JSON.stringify({ url: currentUrl }),
    });
    const data = await res.json();

    if (data.error && !data.total) {
      resultEl.innerHTML = `<div class="error-box">${data.error}</div>`;
      resultEl.style.display = "block";
      return;
    }

    const avg = data.avg_scores || {};
    let html = "";

    // Product title
    if (data.title) {
      html += `<div style="font-weight:700;margin-bottom:8px;font-size:13px">${data.title}</div>`;
    }

    // Verdict
    html += `
      <div class="verdict ${data.overall}">
        <div class="icon">${data.emoji || verdictEmoji(data.overall)}</div>
        <div>
          <strong>Overall: ${data.overall}</strong>
          <p>${data.action}</p>
          <p style="margin-top:3px">
            Avg Compound: ${fmt(data.avg_compound)} &nbsp;|&nbsp;
            Pos: ${fmt(avg.pos)} &nbsp;|&nbsp;
            Neu: ${fmt(avg.neu)} &nbsp;|&nbsp;
            Neg: ${fmt(avg.neg)}
          </p>
        </div>
      </div>`;

    // Partial scrape warning
    if (data.error) {
      html += `<div class="error-box" style="margin-bottom:6px">⚠ ${data.error}</div>`;
    }

    // Stats
    html += `
      <div class="stats">
        <div class="stat pos"><div class="n">${data.positive}</div><div class="l">Positive</div></div>
        <div class="stat neu"><div class="n">${data.neutral}</div><div class="l">Neutral</div></div>
        <div class="stat neg"><div class="n">${data.negative}</div><div class="l">Negative</div></div>
        <div class="stat fake"><div class="n">${data.fake}</div><div class="l">Fake</div></div>
        <div class="stat"><div class="n">${data.total}</div><div class="l">Total</div></div>
      </div>`;

    // Aspect-based sentiment
    if (data.aspects && Object.keys(data.aspects).length) {
      const aEmoji = { Positive: "😊", Neutral: "😐", Negative: "😞" };
      const aCards = Object.entries(data.aspects).map(([name, a]) => {
        const clr = a.verdict === "Positive" ? "#2e7d32" : a.verdict === "Negative" ? "#b71c1c" : "#e65100";
        return `<div style="margin-bottom:5px;font-size:11px">
          <span style="font-weight:700">${name}</span>:
          <span style="color:${clr}">${aEmoji[a.verdict]||"😐"} ${a.verdict}</span>
          <span style="color:#999"> · ${a.total} mentions</span>
        </div>`;
      }).join("");
      html += `<details style="margin-top:8px">
        <summary>🔍 Aspect Breakdown</summary>
        <div style="margin-top:6px">${aCards}</div>
      </details>`;
    }

    // Review breakdown (collapsible)
    if (data.reviews && data.reviews.length) {
      const items = data.reviews.map(r => `
        <div class="review-item ${r.label}">
          <div class="rv-meta">${badge(r.label)} &nbsp; compound: ${fmt(r.scores.compound)}</div>
          ${r.text}
        </div>`).join("");
      html += `
        <details>
          <summary>Review breakdown (${data.reviews.length} genuine)</summary>
          <div class="review-list">${items}</div>
        </details>`;
    }

    // Fake reviews (collapsible)
    if (data.fake_details && data.fake_details.length) {
      const items = data.fake_details.map(f => `
        <div class="review-item" style="border-color:#ab47bc">
          ${f.text}
          <div style="font-size:10px;color:#6a1b9a;margin-top:3px">
            ⚠ ${f.label} · ${f.method}
          </div>
        </div>`).join("");
      html += `
        <details>
          <summary>Fake reviews (${data.fake_details.length})</summary>
          <div class="review-list">${items}</div>
        </details>`;
    }

    // Open in full app link
    html += `<div class="action-bar">
      <a href="${API}" target="_blank" style="color:#3d2fa0">Open full app ↗</a>
    </div>`;

    resultEl.innerHTML = html;
    resultEl.style.display = "block";

  } catch (err) {
    resultEl.innerHTML = `<div class="error-box">Cannot reach Opinion Miner server.<br>
      Make sure Flask is running on <strong>localhost:5000</strong>.</div>`;
    resultEl.style.display = "block";
  } finally {
    urlBtn.disabled = false;
    urlBtn.textContent = "Scrape & Analyze";
    document.getElementById("url-spinner").style.display = "none";
  }
});
