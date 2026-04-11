const fileInput = document.getElementById("file");
const dropZone = document.getElementById("dropZone");
const fileMeta = document.getElementById("fileMeta");
const blurInput = document.getElementById("blur");
const blurValue = document.getElementById("blurValue");
const modeInput = document.getElementById("mode");
const colorBox = document.getElementById("colorBox");
const colorInput = document.getElementById("bgcolor");
const qualityInput = document.getElementById("quality");
const enhanceFaceInput = document.getElementById("enhanceFace");
const aiGoalInput = document.getElementById("aiGoal");
const aiSuggestBtn = document.getElementById("aiSuggestBtn");
const convertBtn = document.getElementById("convertBtn");
const resetBtn = document.getElementById("resetBtn");
const copyLinkBtn = document.getElementById("copyLinkBtn");
const statusText = document.getElementById("statusText");
const preview = document.getElementById("preview");
const placeholder = document.getElementById("placeholder");
const downloadBtn = document.getElementById("downloadBtn");

let currentFile = null;
let previewURL = null;

function setStatus(text, tone = "info") {
  statusText.textContent = text;
  statusText.dataset.tone = tone;
}

function setBusyState(isBusy, label = "Convert Image") {
  convertBtn.disabled = isBusy;
  aiSuggestBtn.disabled = isBusy;
  convertBtn.textContent = isBusy ? "Processing..." : label;
}

function formatBytes(bytes) {
  if (!bytes) return "0 B";
  const sizes = ["B", "KB", "MB", "GB"];
  const i = Math.min(Math.floor(Math.log(bytes) / Math.log(1024)), sizes.length - 1);
  const value = bytes / Math.pow(1024, i);
  return `${value.toFixed(value >= 10 ? 0 : 1)} ${sizes[i]}`;
}

function setDefaultQuality(width, height) {
  const maxSide = Math.max(width, height);
  if (maxSide >= 3400) {
    qualityInput.value = "ultra";
  } else if (maxSide >= 2000) {
    qualityInput.value = "hd";
  } else {
    qualityInput.value = "normal";
  }
}

function handleFileSelection(file) {
  if (!file || !file.type.startsWith("image/")) {
    setStatus("Please choose an image file (JPG/PNG/WebP).", "warn");
    return;
  }

  currentFile = file;

  const dt = new DataTransfer();
  dt.items.add(file);
  fileInput.files = dt.files;

  const tempURL = URL.createObjectURL(file);
  const img = new Image();
  img.onload = () => {
    fileMeta.textContent = `${file.name} | ${formatBytes(file.size)} | ${img.width}x${img.height}`;
    setDefaultQuality(img.width, img.height);
    URL.revokeObjectURL(tempURL);
  };
  img.src = tempURL;

  setStatus("Ready to convert. You can also click AI Auto Tune.", "info");
}

function applySuggestedSettings(settings) {
  if (!settings) return;

  if (settings.mode) {
    modeInput.value = settings.mode;
    colorBox.style.display = settings.mode === "color" ? "block" : "none";
  }
  if (settings.blur !== undefined) {
    blurInput.value = settings.blur;
    blurValue.textContent = String(settings.blur);
  }
  if (settings.quality) {
    qualityInput.value = settings.quality;
  }
  if (settings.bgcolor) {
    colorInput.value = settings.bgcolor;
  }
  if (settings.enhance_face !== undefined) {
    enhanceFaceInput.checked = Boolean(settings.enhance_face);
  }
}

async function aiSuggest() {
  if (!currentFile) {
    setStatus("Upload an image first to use AI Auto Tune.", "warn");
    return;
  }

  setBusyState(true, "Convert Image");
  setStatus("Requesting AI recommendations...", "info");

  try {
    const formData = new FormData();
    formData.append("file", currentFile);
    formData.append("goal", aiGoalInput.value || "balanced");

    const res = await fetch("/ai/suggest-settings", {
      method: "POST",
      body: formData,
    });

    if (!res.ok) {
      let detail = "AI suggestion failed.";
      try {
        const body = await res.json();
        detail = body.detail || detail;
      } catch (_) {
        // ignore parse failure
      }
      throw new Error(detail);
    }

    const data = await res.json();
    applySuggestedSettings(data.settings);
    const source = data.source === "ai" ? "AI API" : "local fallback";
    const reason = data.settings?.reason ? ` ${data.settings.reason}` : "";
    setStatus(`Settings updated from ${source}.${reason}`, "success");
  } catch (err) {
    console.error(err);
    setStatus(err.message || "AI suggestion failed.", "error");
  } finally {
    setBusyState(false, "Convert Image");
  }
}

async function convert() {
  if (!currentFile) {
    setStatus("Please upload an image first.", "warn");
    dropZone.focus();
    return;
  }

  setBusyState(true, "Convert Image");
  setStatus("Processing on the server. This may take a few seconds...", "info");

  try {
    const formData = new FormData();
    formData.append("file", currentFile);
    formData.append("blur", blurInput.value);
    formData.append("mode", modeInput.value);
    formData.append("bgcolor", colorInput.value);
    formData.append("quality", qualityInput.value);
    formData.append("enhance_face", enhanceFaceInput.checked);

    const res = await fetch("/convert", {
      method: "POST",
      body: formData,
    });

    if (!res.ok) {
      let detail = "Conversion failed. Please try again.";
      try {
        const body = await res.json();
        detail = body.detail || detail;
      } catch (_) {
        // ignore parse errors
      }
      throw new Error(detail);
    }

    const blob = await res.blob();
    if (previewURL) URL.revokeObjectURL(previewURL);
    previewURL = URL.createObjectURL(blob);

    preview.src = previewURL;
    preview.style.display = "block";
    placeholder.style.display = "none";

    const cleanName = currentFile.name.replace(/\.[^/.]+$/, "") || "insta-no-crop";
    downloadBtn.href = previewURL;
    downloadBtn.download = `${cleanName}_nocrop.png`;
    downloadBtn.style.display = "inline-block";

    setStatus("Done. Download or copy the preview link.", "success");
  } catch (err) {
    console.error(err);
    setStatus(err.message || "Something went wrong.", "error");
  } finally {
    setBusyState(false, "Convert Image");
  }
}

function resetUI() {
  currentFile = null;
  if (previewURL) URL.revokeObjectURL(previewURL);
  previewURL = null;
  fileInput.value = "";
  fileMeta.textContent = "No image selected yet.";
  preview.src = "";
  preview.style.display = "none";
  placeholder.style.display = "flex";
  downloadBtn.style.display = "none";
  aiGoalInput.value = "";
  setStatus("Reset complete. Drop another image to start.", "info");
}

function copyPreviewURL() {
  if (!previewURL) {
    setStatus("Generate a preview first.", "warn");
    return;
  }
  navigator.clipboard
    .writeText(previewURL)
    .then(() => setStatus("Preview URL copied to clipboard.", "success"))
    .catch(() => setStatus("Could not copy. Please copy manually.", "warn"));
}

fileInput.addEventListener("change", (e) => handleFileSelection(e.target.files[0]));

dropZone.addEventListener("dragover", (e) => {
  e.preventDefault();
  dropZone.classList.add("dragging");
});

dropZone.addEventListener("dragleave", () => dropZone.classList.remove("dragging"));

dropZone.addEventListener("drop", (e) => {
  e.preventDefault();
  dropZone.classList.remove("dragging");
  if (e.dataTransfer.files.length) {
    handleFileSelection(e.dataTransfer.files[0]);
  }
});

dropZone.addEventListener("click", () => fileInput.click());

modeInput.addEventListener("change", (e) => {
  colorBox.style.display = e.target.value === "color" ? "block" : "none";
});

blurInput.addEventListener("input", (e) => {
  blurValue.textContent = e.target.value;
});

aiSuggestBtn.addEventListener("click", aiSuggest);
convertBtn.addEventListener("click", convert);
resetBtn.addEventListener("click", resetUI);
copyLinkBtn.addEventListener("click", copyPreviewURL);

setStatus("Ready when you are.", "info");
