const $ = (s) => document.querySelector(s);
const show = (el) => el.classList.remove("hidden");
const hide = (el) => el.classList.add("hidden");

// Upload is the default (primary) mode; YouTube URL is secondary
let mode = "file", lang = "english", file = null, jobId = null, result = null, tab = "summary";

/* ---------- segmented controls ---------- */
function seg(containerSel, onPick) {
  $(containerSel).addEventListener("click", (e) => {
    const b = e.target.closest("button");
    if (!b) return;
    $(containerSel).querySelectorAll("button").forEach((x) => x.classList.remove("active"));
    b.classList.add("active");
    onPick(b);
  });
}

function setMode(m) {
  mode = m;
  document.querySelectorAll("#srcTabs button").forEach((x) =>
    x.classList.toggle("active", x.dataset.mode === m)
  );
  if (m === "file") { show($("#fileBox")); hide($("#urlBox")); }
  else { show($("#urlBox")); hide($("#fileBox")); }
}
seg("#srcTabs", (b) => setMode(b.dataset.mode));
setMode("file"); // make sure initial state = upload first

seg("#langTabs", (b) => (lang = b.dataset.lang));

/* ---------- file drop ---------- */
const drop = $("#drop");
function setFile(f) {
  file = f;
  $("#fileName").textContent = "✅ " + f.name;
  show($("#fileName"));
}
$("#fileInput").addEventListener("change", (e) => e.target.files[0] && setFile(e.target.files[0]));
["dragenter", "dragover"].forEach((ev) => drop.addEventListener(ev, (e) => { e.preventDefault(); drop.classList.add("over"); }));
["dragleave", "drop"].forEach((ev) => drop.addEventListener(ev, (e) => { e.preventDefault(); drop.classList.remove("over"); }));
drop.addEventListener("drop", (e) => e.dataTransfer.files[0] && setFile(e.dataTransfer.files[0]));

/* ---------- view switching ---------- */
function view(name) {
  ["home", "processing", "results"].forEach((v) => hide($("#" + v)));
  show($("#" + name));
  name === "results" ? show($("#newBtn")) : hide($("#newBtn"));
  window.scrollTo({ top: 0, behavior: "smooth" });
}
$("#newBtn").onclick = () => {
  jobId = null; result = null;
  $("#msgs").innerHTML = '<div class="msg bot">Hi! Ask me anything about this video. I will answer only from its transcript.</div>';
  show($("#suggest"));
  setMode("file");
  view("home");
};

/* ---------- analyze ---------- */
$("#analyzeBtn").onclick = async () => {
  const err = $("#homeErr");
  hide(err);
  const fd = new FormData();
  fd.append("language", lang);
  if (mode === "url") {
    const u = $("#urlInput").value.trim();
    if (!u) return showErr("Enter a YouTube URL or upload a file.");
    fd.append("url", u);
  } else {
    if (!file) return showErr("Please choose a video or audio file first.");
    fd.append("file", file);
  }
  $("#analyzeBtn").disabled = true;
  try {
    const r = await fetch("/api/analyze", { method: "POST", body: fd });
    if (!r.ok) throw new Error((await r.json()).detail || "Request failed");
    jobId = (await r.json()).job_id;
    buildSteps(["Audio", "Transcribe", "Understand", "Extract", "Index"]);
    setProgress(2, "Starting...", 0);
    view("processing");
    poll();
  } catch (e) {
    showErr(e.message);
  } finally {
    $("#analyzeBtn").disabled = false;
  }
};
function showErr(msg) { const e = $("#homeErr"); e.textContent = "❌ " + msg; show(e); }

function buildSteps(list) {
  $("#stepsList").innerHTML = list.map((s, i) => `<li data-i="${i}"><i>${i + 1}</i><span>${s}</span></li>`).join("");
}
function setProgress(p, msg, step) {
  $("#barFill").style.width = p + "%";
  $("#pct").textContent = p + "%";
  $("#procMsg").textContent = msg;
  document.querySelectorAll("#stepsList li").forEach((li) => {
    const i = +li.dataset.i;
    li.className = i < step ? "done" : i === step ? "on" : "";
    if (i < step) li.querySelector("i").textContent = "✓";
  });
}

async function poll() {
  try {
    const j = await (await fetch("/api/jobs/" + jobId)).json();
    if (j.status === "error") {
      view("home");
      let m = j.error || "Something went wrong";
      if (/403|youtube|download/i.test(m)) {
        m = "YouTube blocked the download. Please upload the same video file and try again.";
        setMode("file"); // auto-switch to the upload option
      }
      return showErr(m);
    }
    setProgress(j.progress, j.message, j.step);
    if (j.status === "done") {
      setProgress(100, "Done ✨", 5);
      result = j.result;
      return setTimeout(renderResults, 500);
    }
  } catch (e) { /* transient, keep polling */ }
  setTimeout(poll, 1500);
}

/* ---------- markdown-lite ---------- */
const esc = (s) => s.replace(/[&<>]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;" }[c]));
function inline(s) { return esc(s).replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>").replace(/\*(.+?)\*/g, "<em>$1</em>"); }
function md(text) {
  const lines = text.split("\n").map((l) => l.trim()).filter(Boolean);
  let html = "", list = [], n = 0;
  const flush = () => { if (list.length) { html += "<ul>" + list.join("") + "</ul>"; list = []; n = 0; } };
  for (const l of lines) {
    const m = l.match(/^(?:[-*•]|\d+[.)])\s+(.*)/);
    if (m) { n++; list.push(`<li><span class="n">${n}</span>${inline(m[1])}</li>`); }
    else { flush(); html += `<p>${inline(l.replace(/^#+\s*/, ""))}</p>`; }
  }
  flush();
  return html;
}

/* ---------- results ---------- */
function renderResults() {
  $("#resTitle").textContent = result.title.replace(/["*]/g, "");
  const words = result.transcript.split(/\s+/).length;
  $("#chips").innerHTML = [
    ["📝 Words", words.toLocaleString()],
    ["⏱ Read time", Math.max(1, Math.round(words / 200)) + " min"],
    ["🌐 Mode", lang],
    ["📚 Knowledge base", "Ready"],
  ].map(([k, v]) => `<span class="chip">${k}: <b>${v}</b></span>`).join("");
  tab = "summary";
  document.querySelectorAll("#resTabs button").forEach((b) => b.classList.toggle("active", b.dataset.t === tab));
  renderPanel();
  view("results");
}
function renderPanel() {
  const body = $("#panelBody");
  const t = result[tab];
  body.className = tab === "transcript" ? "md tx" : "md";
  body.innerHTML = tab === "transcript" ? "" : md(t);
  if (tab === "transcript") body.textContent = t;
  body.style.animation = "none"; body.offsetHeight; body.style.animation = "";
}
seg("#resTabs", (b) => { tab = b.dataset.t; renderPanel(); });
$("#copyBtn").onclick = async (e) => {
  await navigator.clipboard.writeText(result[tab]);
  e.target.textContent = "Copied ✓"; setTimeout(() => (e.target.textContent = "Copy"), 1200);
};
$("#dlBtn").onclick = () => {
  const a = document.createElement("a");
  a.href = URL.createObjectURL(new Blob([result[tab]], { type: "text/plain" }));
  a.download = tab + ".txt"; a.click();
};

/* ---------- chat ---------- */
function addMsg(text, who) {
  const d = document.createElement("div");
  d.className = "msg " + who; d.textContent = text;
  $("#msgs").appendChild(d); $("#msgs").scrollTop = 1e9;
  return d;
}
async function ask(q) {
  if (!q.trim() || !jobId) return;
  addMsg(q, "me");
  hide($("#suggest"));
  const t = document.createElement("div");
  t.className = "msg bot typing"; t.innerHTML = "<span></span><span></span><span></span>";
  $("#msgs").appendChild(t); $("#msgs").scrollTop = 1e9;
  try {
    const r = await fetch("/api/chat", {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ job_id: jobId, question: q }),
    });
    const j = await r.json();
    t.remove();
    addMsg(r.ok ? j.answer : "⚠️ " + (j.detail || "Error"), "bot");
  } catch (e) { t.remove(); addMsg("⚠️ Network error", "bot"); }
}
$("#chatForm").onsubmit = (e) => { e.preventDefault(); const v = $("#chatInput").value; $("#chatInput").value = ""; ask(v); };
$("#suggest").onclick = (e) => e.target.tagName === "BUTTON" && ask(e.target.textContent);