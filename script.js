/* === ChiralSense Frontend Logic === */

const DOXO_SMILES =
  "CC1=C2C(=C(C=C1O)O)C(=O)C3=C(C2=O)C=C(C=C3O)O[C@H]4C[C@H](O)[C@@H](O[C@@H]5C[C@H](N(C)C)[C@@H](O)[C@H](O)C5O)O4";

/* ── DOM refs ── */
const smilesInput    = document.getElementById("smiles-input");
const analyzeBtn     = document.getElementById("analyze-btn");
const loadDoxoBtn    = document.getElementById("load-doxo-btn");
const clearBtn       = document.getElementById("clear-btn");
const loading        = document.getElementById("loading");
const errorBanner    = document.getElementById("error-banner");
const errorMsg       = document.getElementById("error-msg");
const resultsSection = document.getElementById("results-section");

/* Stats */
const statChiral  = document.getElementById("stat-chiral");
const statR       = document.getElementById("stat-r");
const statS       = document.getElementById("stat-s");
const statAtoms   = document.getElementById("stat-atoms");
const statFormula = document.getElementById("stat-formula");

/* Table & mol */
const chiralTbody = document.getElementById("chiral-tbody");
const molDisplay  = document.getElementById("mol-display");

/* ── Helpers ── */
function showLoading(state) {
  loading.classList.toggle("hidden", !state);
  analyzeBtn.classList.toggle("loading", state);
  analyzeBtn.querySelector(".btn-text").textContent = state ? "Analyzing…" : "Analyze";
}

function showError(msg) {
  errorBanner.classList.remove("hidden");
  errorMsg.textContent = msg;
  resultsSection.classList.add("hidden");
}

function clearError() {
  errorBanner.classList.add("hidden");
  errorMsg.textContent = "";
}

function animateCount(el, target) {
  const isNum = !isNaN(target);
  if (!isNum) { el.textContent = target; return; }
  let start = 0;
  const duration = 600;
  const step = Math.ceil(target / (duration / 16));
  const timer = setInterval(() => {
    start = Math.min(start + step, target);
    el.textContent = start;
    if (start >= target) clearInterval(timer);
  }, 16);
}

/* ── Load example ── */
loadDoxoBtn.addEventListener("click", () => {
  smilesInput.value = DOXO_SMILES;
  smilesInput.focus();
});

/* ── Clear ── */
clearBtn.addEventListener("click", () => {
  smilesInput.value = "";
  resultsSection.classList.add("hidden");
  clearError();
  molDisplay.innerHTML = `
    <div class="mol-placeholder">
      <span>🔬</span>
      <p>Molecule will appear here after analysis</p>
    </div>`;
  smilesInput.focus();
});

/* ── Analyze ── */
async function runAnalysis() {
  const smiles = smilesInput.value.trim();
  if (!smiles) {
    showError("Please enter a SMILES string before analyzing.");
    return;
  }

  clearError();
  showLoading(true);
  resultsSection.classList.add("hidden");

  try {
    const res = await fetch("/analyze", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ smiles }),
    });

    const data = await res.json();

    if (!res.ok) {
      showError(data.error || "An unexpected error occurred.");
      return;
    }

    renderResults(data);
  } catch (err) {
    showError("Network error — could not reach the server. Please try again.");
    console.error(err);
  } finally {
    showLoading(false);
  }
}

analyzeBtn.addEventListener("click", runAnalysis);

/* Allow Enter key (Ctrl+Enter) to trigger analysis */
smilesInput.addEventListener("keydown", (e) => {
  if (e.key === "Enter" && (e.ctrlKey || e.metaKey)) runAnalysis();
});

/* ── Render Results ── */
function renderResults(data) {
  const centers  = data.chiral_centers || [];
  const rCount   = centers.filter(c => c.configuration === "R").length;
  const sCount   = centers.filter(c => c.configuration === "S").length;

  /* Stats */
  animateCount(statChiral, data.num_chiral_centers);
  animateCount(statR, rCount);
  animateCount(statS, sCount);
  animateCount(statAtoms, data.num_atoms);
  statFormula.textContent = data.formula || "—";

  /* Table rows */
  chiralTbody.innerHTML = "";
  if (centers.length === 0) {
    chiralTbody.innerHTML = `<tr><td colspan="4" style="text-align:center;color:var(--text-muted);padding:20px;">No chiral centers found.</td></tr>`;
  } else {
    centers.forEach((c, i) => {
      const configClass =
        c.configuration === "R" ? "config-R" :
        c.configuration === "S" ? "config-S" : "config-other";

      const row = document.createElement("tr");
      row.style.animationDelay = `${i * 50}ms`;
      row.innerHTML = `
        <td>${i + 1}</td>
        <td>${c.atom_index}</td>
        <td>${c.element}</td>
        <td><span class="config-badge ${configClass}">${c.configuration}</span></td>
      `;
      chiralTbody.appendChild(row);
    });
  }

  /* Molecule SVG */
  if (data.molecule_svg) {
    const svgBytes = atob(data.molecule_svg);
    /* Inject SVG directly, not via <img> so it scales properly */
    molDisplay.innerHTML = svgBytes;
    /* Patch SVG colors for dark background */
    const svgEl = molDisplay.querySelector("svg");
    if (svgEl) {
      svgEl.style.background = "transparent";
      svgEl.querySelectorAll("text, line, path, circle, rect").forEach(el => {
        const fill = el.getAttribute("fill");
        const stroke = el.getAttribute("stroke");
        if (fill === "#FFFFFF" || fill === "white") el.setAttribute("fill", "transparent");
        if (stroke === "#000000" || stroke === "black") el.setAttribute("stroke", "#c8d6e5");
      });
    }
  } else {
    molDisplay.innerHTML = `<div class="mol-placeholder"><span>⚠</span><p>Could not render molecule.</p></div>`;
  }

  /* Show section */
  resultsSection.classList.remove("hidden");
  resultsSection.scrollIntoView({ behavior: "smooth", block: "start" });
}

/* ── Auto-analyze on page load if SMILES pre-filled ── */
window.addEventListener("DOMContentLoaded", () => {
  if (smilesInput.value.trim()) {
    setTimeout(runAnalysis, 400);
  }
});
