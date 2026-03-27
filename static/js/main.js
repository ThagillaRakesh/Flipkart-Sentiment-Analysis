/* main.js — Opinion Miner frontend logic */

"use strict";

// ── Helpers ───────────────────────────────────────────────────────────────────

function badge(label) {
  const cls = label.toLowerCase();
  return `<span class="badge badge-${cls}">${label}</span>`;
}

function showSpinner(id) {
  document.getElementById(id).style.display = "flex";
}
function hideSpinner(id) {
  document.getElementById(id).style.display = "none";
}

function showPanel(id) {
  document.getElementById(id).style.display = "block";
}

function b64img(src, alt) {
  return src ? `<img src="data:image/png;base64,${src}" alt="${alt}">` : "";
}

function verdictEmoji(label, apiEmoji) {
  if (apiEmoji) return apiEmoji;
  return label === "Positive" ? "😊" : label === "Negative" ? "😞" : "😐";
}

/* Play the verdict audio and render an inline player for replay */
function renderAudioPlayer(audioUrl) {
  if (!audioUrl) return "";
  // Auto-play
  const a = new Audio(audioUrl);
  a.play().catch(() => {}); // ignore autoplay block
  return `
    <div class="audio-player">
      <span>🔊 Verdict Audio:</span>
      <audio controls src="${audioUrl}" style="vertical-align:middle;height:28px;"></audio>
    </div>`;
}

// ── Text Analysis ─────────────────────────────────────────────────────────────

document.getElementById("text-form").addEventListener("submit", async (e) => {
  e.preventDefault();

  const text = document.getElementById("text-input").value.trim();
  if (!text) return;

  const btn = e.target.querySelector("button");
  btn.disabled = true;
  showSpinner("text-spinner");
  document.getElementById("text-result").style.display = "none";

  try {
    const res  = await fetch("/analyze", {
      method:  "POST",
      headers: { "Content-Type": "application/json" },
      body:    JSON.stringify({ text }),
    });
    const data = await res.json();

    if (data.error) {
      document.getElementById("text-result").innerHTML =
        `<div class="error-box">${data.error}</div>`;
    } else {
      const s = data.scores;
      document.getElementById("text-result").innerHTML = `
        <div class="verdict ${data.label}">
          <div class="icon">${verdictEmoji(data.label, data.emoji)}</div>
          <div class="text">
            <strong>Sentiment: ${data.label}</strong>
            <p>Compound: ${s.compound.toFixed(3)} &nbsp;|&nbsp;
               Positive: ${s.pos.toFixed(3)} &nbsp;|&nbsp;
               Neutral: ${s.neu.toFixed(3)} &nbsp;|&nbsp;
               Negative: ${s.neg.toFixed(3)}</p>
          </div>
        </div>
        ${renderAudioPlayer(data.audio_url)}
      `;
    }
    showPanel("text-result");
  } catch (err) {
    document.getElementById("text-result").innerHTML =
      `<div class="error-box">Request failed: ${err.message}</div>`;
    showPanel("text-result");
  } finally {
    btn.disabled = false;
    hideSpinner("text-spinner");
  }
});

// ── URL Analysis ──────────────────────────────────────────────────────────────

document.getElementById("url-form").addEventListener("submit", async (e) => {
  e.preventDefault();

  const url = document.getElementById("url-input").value.trim();
  if (!url) return;

  const btn = e.target.querySelector("button");
  btn.disabled = true;
  showSpinner("url-spinner");
  document.getElementById("url-result").style.display = "none";

  try {
    const res  = await fetch("/analyze-url", {
      method:  "POST",
      headers: { "Content-Type": "application/json" },
      body:    JSON.stringify({ url }),
    });
    const data = await res.json();

    if (data.error && !data.total) {
      document.getElementById("url-result").innerHTML =
        `<div class="error-box">${data.error}</div>`;
      showPanel("url-result");
      return;
    }

    // Build HTML
    let html = "";

    // Platform badge + product header
    const platformLabel = data.platform || "Flipkart";
    const img  = data.images && data.images[0]
                   ? `<img class="product-img" src="${data.images[0]}" alt="product">`
                   : "";
    const star = data.rating ? `⭐ ${data.rating}` : "";
    html += `
      <span class="platform-tag ${platformLabel}">${platformLabel}</span>
      <div style="display:flex;align-items:center;gap:1rem;margin-bottom:1rem">
        ${img}
        <div>
          <strong style="font-size:1.05rem">${data.title || platformLabel + " Product"}</strong>
          <div style="font-size:.9rem;color:#555;margin-top:.3rem">${star}</div>
        </div>
      </div>`;

    // Overall verdict + audio
    const avg = data.avg_scores || {};
    const ac  = typeof data.avg_compound === "number" ? data.avg_compound.toFixed(3) : "—";
    const ap  = typeof avg.pos === "number" ? avg.pos.toFixed(3) : "—";
    const an  = typeof avg.neu === "number" ? avg.neu.toFixed(3) : "—";
    const ang = typeof avg.neg === "number" ? avg.neg.toFixed(3) : "—";
    html += `
      <div class="verdict ${data.overall}">
        <div class="icon">${verdictEmoji(data.overall, data.emoji)}</div>
        <div class="text">
          <strong>Overall: ${data.overall}</strong>
          <p>${data.action}</p>
          <p style="font-size:.85rem;margin-top:.3rem;opacity:.85">
            Avg Compound: ${ac} &nbsp;|&nbsp;
            Positive: ${ap} &nbsp;|&nbsp;
            Neutral: ${an} &nbsp;|&nbsp;
            Negative: ${ang}
          </p>
        </div>
      </div>
      ${renderAudioPlayer(data.audio_url)}`;

    // Partial scraping warning
    if (data.error) {
      html += `<div class="error-box" style="margin-bottom:.8rem">⚠ ${data.error}</div>`;
    }

    // Stats grid
    html += `
      <div class="summary-grid">
        <div class="stat-box pos">
          <div class="count">${data.positive}</div>
          <div class="label">Positive</div>
        </div>
        <div class="stat-box neu">
          <div class="count">${data.neutral}</div>
          <div class="label">Neutral</div>
        </div>
        <div class="stat-box neg">
          <div class="count">${data.negative}</div>
          <div class="label">Negative</div>
        </div>
        <div class="stat-box fake">
          <div class="count">${data.fake}</div>
          <div class="label">Fake</div>
        </div>
        <div class="stat-box">
          <div class="count">${data.total}</div>
          <div class="label">Total</div>
        </div>
      </div>`;

    // Charts
    const charts = data.charts || {};
    html += `<div class="charts">
      ${b64img(charts.bar,    "Sentiment bar chart")}
      ${b64img(charts.scores, "Score chart")}
      ${charts.wc_pos ? b64img(charts.wc_pos, "Positive word cloud") : ""}
      ${charts.wc_neg ? b64img(charts.wc_neg, "Negative word cloud") : ""}
    </div>`;

    // Aspect-based sentiment cards
    if (data.aspects && Object.keys(data.aspects).length) {
      const aspectEmoji = { Positive: "😊", Neutral: "😐", Negative: "😞" };
      const cards = Object.entries(data.aspects).map(([name, a]) => {
        const total = a.total || 1;
        const pw = Math.round((a.positive / total) * 100);
        const nw = Math.round((a.neutral  / total) * 100);
        const ngw= Math.round((a.negative / total) * 100);
        return `
          <div class="aspect-card ${a.verdict}">
            <div class="aspect-name">${name}</div>
            <div class="aspect-verdict">${aspectEmoji[a.verdict] || "😐"} ${a.verdict}</div>
            <div class="aspect-bar">
              <div class="bar-pos" style="width:${pw}%"></div>
              <div class="bar-neu" style="width:${nw}%"></div>
              <div class="bar-neg" style="width:${ngw}%"></div>
            </div>
            <div class="aspect-counts">👍${a.positive} 😐${a.neutral} 👎${a.negative} · ${a.total} mentions</div>
          </div>`;
      }).join("");
      html += `
        <div class="aspects-section">
          <h3>🔍 Aspect-Based Sentiment</h3>
          <div class="aspects-grid">${cards}</div>
        </div>`;
    }

    // Per-review breakdown (collapsible)
    if (data.reviews && data.reviews.length) {
      const items = data.reviews.map(r => `
        <div class="review-item ${r.label}">
          <div class="rv-label">${badge(r.label)} &nbsp; compound: ${r.scores.compound.toFixed(3)}</div>
          ${r.text}
        </div>`).join("");
      html += `
        <details>
          <summary>Review breakdown (${data.reviews.length} genuine reviews)</summary>
          <div style="margin-top:.8rem">${items}</div>
        </details>`;
    }

    // Fake reviews (collapsible)
    if (data.fake_details && data.fake_details.length) {
      const items = data.fake_details.map(f => `
        <div class="fake-item">
          ${f.text}
          <div class="reasons">⚠ ${f.label} · detected by ${f.method}</div>
        </div>`).join("");
      html += `
        <details>
          <summary>Fake reviews detected (${data.fake_details.length})</summary>
          <div style="margin-top:.8rem">${items}</div>
        </details>`;
    }

    document.getElementById("url-result").innerHTML = html;
    showPanel("url-result");

  } catch (err) {
    document.getElementById("url-result").innerHTML =
      `<div class="error-box">Request failed: ${err.message}</div>`;
    showPanel("url-result");
  } finally {
    btn.disabled = false;
    hideSpinner("url-spinner");
  }
});
