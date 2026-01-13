async function upload() {
  const fileInput = document.getElementById("file");
  const blurInput = document.getElementById("blur");
  const modeInput = document.getElementById("mode");
  const colorInput = document.getElementById("bgcolor");
  const qualityInput = document.getElementById("quality");

  const preview = document.getElementById("preview");
  const downloadBtn = document.getElementById("downloadBtn");
  const convertBtn = document.getElementById("convertBtn");

  if (!fileInput.files.length) {
    alert("Please upload an image first");
    return;
  }

  convertBtn.disabled = true;
  convertBtn.innerText = "⏳ Processing...";
  preview.style.display = "none";
  downloadBtn.style.display = "none";

  try {
    const formData = new FormData();
    formData.append("file", fileInput.files[0]);
    formData.append("blur", blurInput.value);
    formData.append("mode", modeInput.value);
    formData.append("bgcolor", colorInput.value);
    formData.append("quality", qualityInput.value);
    const enhanceFace = document.getElementById("enhanceFace").checked;

formData.append("enhance_face", enhanceFace);

    const res = await fetch("/convert", {
      method: "POST",
      body: formData
    });

    if (!res.ok) {
      throw new Error("Conversion failed");
    }

    const blob = await res.blob();
    const imageURL = URL.createObjectURL(blob);

    preview.src = imageURL;
    preview.style.display = "block";

    downloadBtn.href = imageURL;
    downloadBtn.style.display = "inline-block";

  } catch (err) {
    console.error(err);
    alert("Something went wrong. Please try again.");
  } finally {
    convertBtn.disabled = false;
    convertBtn.innerText = "✨ Convert Image";
  }
}
