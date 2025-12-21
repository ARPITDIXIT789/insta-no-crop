async function upload() {
  const fileInput = document.getElementById("file");
  const btn = document.getElementById("convertBtn");
  const preview = document.getElementById("preview");

  if (!fileInput.files.length) {
    alert("Please select an image first");
    return;
  }

  btn.disabled = true;
  btn.innerText = "Processing...";

  preview.style.display = "none";
  preview.src = "";

  const form = new FormData();
  form.append("file", fileInput.files[0]);

  try {
    const res = await fetch("/api/convert", {
      method: "POST",
      body: form,
      cache: "no-store"
    });

    if (!res.ok) {
      throw new Error("Server error");
    }

    const blob = await res.blob();
    const imgURL = URL.createObjectURL(blob);

    preview.src = imgURL;
    preview.style.display = "block";
  } catch (err) {
    alert("Conversion failed");
    console.error(err);
  } finally {
    btn.disabled = false;
    btn.innerText = "Convert";
  }
}
