(() => {
  "use strict";

  // Same origin when served by FastAPI at /app/. If index.html is opened any other
  // way (file://, another dev server) fall back to the local API, or use ?api=URL.
  const params = new URLSearchParams(location.search);
  const API_BASE = (params.get("api") ||
    (location.protocol.startsWith("http") && location.pathname.startsWith("/app") ? "" : "http://127.0.0.1:8000"))
    .replace(/\/$/, "");

  const MAX_BYTES = 10 * 1024 * 1024;
  const OK_TYPES = ["image/jpeg", "image/png"];
  const $ = (id) => document.getElementById(id);

  const el = {
    tabUpload: $("tabUpload"), tabCamera: $("tabCamera"),
    paneUpload: $("paneUpload"), paneCamera: $("paneCamera"),
    dropzone: $("dropzone"), fileInput: $("fileInput"),
    video: $("video"), cameraBox: document.querySelector(".camera-box"),
    startCamera: $("startCamera"), switchCamera: $("switchCamera"), stopCamera: $("stopCamera"),
    captureBtn: $("captureBtn"), cameraError: $("cameraError"),
    previewBox: $("previewBox"), previewImg: $("previewImg"), clearBtn: $("clearBtn"),
    predictBtn: $("predictBtn"), loader: $("loader"), toasts: $("toasts"),
    emptyState: $("emptyState"), results: $("results"), resultImg: $("resultImg"),
    topClass: $("topClass"), topConf: $("topConf"), topBar: $("topBar"), allClasses: $("allClasses"),
    status: $("status"), statusText: $("statusText"),
  };

  let currentBlob = null;     // the image that will be sent to /predict (upload OR capture)
  let currentName = "image.jpg";
  let currentUrl = null;
  let stream = null;
  let facing = "environment"; // rear camera first (phones); desktops fall back automatically

  /* ---------- helpers ---------- */
  function toast(msg, type = "info", ms = 4500) {
    const t = document.createElement("div");
    t.className = `toast ${type}`; t.textContent = msg;
    el.toasts.appendChild(t);
    setTimeout(() => t.remove(), ms);
  }

  function setImage(blob, name) {
    if (currentUrl) URL.revokeObjectURL(currentUrl);
    currentBlob = blob; currentName = name || "image.jpg";
    currentUrl = URL.createObjectURL(blob);
    el.previewImg.src = currentUrl;
    el.previewBox.hidden = false;
    el.predictBtn.disabled = false;
  }

  function clearImage() {
    if (currentUrl) URL.revokeObjectURL(currentUrl);
    currentBlob = null; currentUrl = null;
    el.previewImg.removeAttribute("src");
    el.previewBox.hidden = true;
    el.predictBtn.disabled = true;
    el.fileInput.value = "";
    el.results.hidden = true; el.emptyState.hidden = false;
  }

  function validate(file) {
    if (!OK_TYPES.includes(file.type) && !/\.(jpe?g|png)$/i.test(file.name || "")) {
      toast("Unsupported file. Please choose a JPG, JPEG or PNG image.", "error"); return false;
    }
    if (file.size > MAX_BYTES) { toast("Image is larger than 10 MB.", "error"); return false; }
    if (file.size === 0) { toast("That file is empty.", "error"); return false; }
    return true;
  }

  /* ---------- tabs ---------- */
  function showTab(which) {
    const cam = which === "camera";
    el.tabUpload.classList.toggle("active", !cam); el.tabCamera.classList.toggle("active", cam);
    el.tabUpload.setAttribute("aria-selected", String(!cam)); el.tabCamera.setAttribute("aria-selected", String(cam));
    el.paneUpload.hidden = cam; el.paneCamera.hidden = !cam;
    if (!cam) stopStream();
  }
  el.tabUpload.onclick = () => showTab("upload");
  el.tabCamera.onclick = () => showTab("camera");

  /* ---------- upload ---------- */
  el.dropzone.onclick = () => el.fileInput.click();
  el.dropzone.onkeydown = (e) => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); el.fileInput.click(); } };
  el.fileInput.onchange = () => { const f = el.fileInput.files[0]; if (f && validate(f)) setImage(f, f.name); };
  ["dragenter", "dragover"].forEach((ev) => el.dropzone.addEventListener(ev, (e) => { e.preventDefault(); el.dropzone.classList.add("drag"); }));
  ["dragleave", "drop"].forEach((ev) => el.dropzone.addEventListener(ev, (e) => { e.preventDefault(); el.dropzone.classList.remove("drag"); }));
  el.dropzone.addEventListener("drop", (e) => { const f = e.dataTransfer.files[0]; if (f && validate(f)) setImage(f, f.name); });
  el.clearBtn.onclick = clearImage;

  /* ---------- camera ---------- */
  function cameraError(msg) { el.cameraError.textContent = msg; el.cameraError.hidden = !msg; }

  function explain(err) {
    switch (err && err.name) {
      case "NotAllowedError": case "SecurityError":
        return "Camera permission was denied. Allow camera access in your browser's address bar and try again.";
      case "NotFoundError": case "OverconstrainedError":
        return "No suitable camera was found on this device.";
      case "NotReadableError":
        return "The camera is in use by another application. Close it and try again.";
      default:
        return "Could not start the camera: " + ((err && err.message) || "unknown error");
    }
  }

  function stopStream() {
    if (stream) stream.getTracks().forEach((t) => t.stop());
    stream = null; el.video.srcObject = null;
    el.cameraBox.classList.remove("live");
    el.captureBtn.disabled = true; el.switchCamera.disabled = true; el.stopCamera.disabled = true;
    el.startCamera.disabled = false;
  }

  async function startStream() {
    cameraError("");
    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
      cameraError("Camera access is not available. Open this page via http://localhost:8000/app/ (or HTTPS) in a modern browser.");
      return;
    }
    stopStream();
    try {
      stream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: { ideal: facing }, width: { ideal: 1280 }, height: { ideal: 960 } }, audio: false,
      });
      el.video.srcObject = stream;
      await el.video.play();
      el.cameraBox.classList.add("live");
      el.captureBtn.disabled = false; el.stopCamera.disabled = false; el.startCamera.disabled = true;
      const devices = await navigator.mediaDevices.enumerateDevices();
      el.switchCamera.disabled = devices.filter((d) => d.kind === "videoinput").length < 2;
    } catch (err) {
      stopStream(); cameraError(explain(err)); toast(explain(err), "error");
    }
  }

  el.startCamera.onclick = startStream;
  el.stopCamera.onclick = stopStream;
  el.switchCamera.onclick = () => { facing = facing === "environment" ? "user" : "environment"; startStream(); };

  el.captureBtn.onclick = () => {
    if (!stream || !el.video.videoWidth) return;
    const c = document.createElement("canvas");
    c.width = el.video.videoWidth; c.height = el.video.videoHeight;
    c.getContext("2d").drawImage(el.video, 0, 0, c.width, c.height);
    c.toBlob((blob) => {
      if (!blob) { toast("Could not capture the image.", "error"); return; }
      setImage(blob, "capture.jpg");
      toast("Image captured. Press “Classify Weed”.", "success", 2500);
    }, "image/jpeg", 0.92);
  };

  window.addEventListener("beforeunload", stopStream);

  /* ---------- prediction (shared by upload + camera) ---------- */
  async function classify() {
    if (!currentBlob) return;
    el.loader.hidden = false; el.predictBtn.disabled = true;
    try {
      const form = new FormData();
      form.append("file", currentBlob, currentName);
      const res = await fetch(`${API_BASE}/predict`, { method: "POST", body: form });
      let data = null;
      try { data = await res.json(); } catch (_) { /* non-JSON error */ }
      if (!res.ok || !data || !data.success) throw new Error((data && data.error) || `Server returned ${res.status}`);
      renderResults(data);
      toast(`Predicted: ${data.predicted_class} (${data.confidence.toFixed(2)}%)`, "success");
    } catch (err) {
      const offline = err instanceof TypeError;
      toast(offline ? "Cannot reach the API. Is the backend running?" : err.message, "error", 6000);
    } finally {
      el.loader.hidden = true; el.predictBtn.disabled = !currentBlob;
    }
  }
  el.predictBtn.onclick = classify;

  function renderResults(d) {
    el.emptyState.hidden = true; el.results.hidden = false;
    el.resultImg.src = currentUrl;
    el.topClass.textContent = d.predicted_class;
    el.topConf.textContent = d.confidence.toFixed(2) + "%";
    el.topBar.style.width = "0%";
    requestAnimationFrame(() => requestAnimationFrame(() => { el.topBar.style.width = d.confidence + "%"; }));

    const sorted = [...d.predictions].sort((a, b) => b.confidence - a.confidence);
    el.allClasses.replaceChildren(...sorted.map((p, i) => {
      const li = document.createElement("li");
      li.className = "class-item" + (i === 0 ? " top" : "");
      const meta = document.createElement("div"); meta.className = "meta";
      const n = document.createElement("span"); n.textContent = p.class;
      const v = document.createElement("span"); v.textContent = p.confidence.toFixed(2) + "%";
      meta.append(n, v);
      const bar = document.createElement("div"); bar.className = "bar";
      const fill = document.createElement("div"); fill.className = "fill";
      bar.appendChild(fill); li.append(meta, bar);
      requestAnimationFrame(() => requestAnimationFrame(() => { fill.style.width = p.confidence + "%"; }));
      return li;
    }));
    el.results.scrollIntoView({ behavior: "smooth", block: "nearest" });
  }

  /* ---------- backend status ---------- */
  async function checkHealth() {
    try {
      const res = await fetch(`${API_BASE}/health`);
      const data = await res.json();
      if (res.ok && data.model_loaded) { el.status.className = "status ok"; el.statusText.textContent = "Model ready"; }
      else { el.status.className = "status bad"; el.statusText.textContent = "Model not loaded"; toast(data.detail || "Model is not loaded.", "error", 8000); }
    } catch (_) {
      el.status.className = "status bad"; el.statusText.textContent = "API offline";
    }
  }
  checkHealth();
})();