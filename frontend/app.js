async function upload() {
  const input = document.getElementById("file");
  if (!input.files.length) {
    alert("Please select an image first");
    return;
  }

  const form = new FormData();
  form.append("file", input.files[0]);

  try {
    const res = await fetch("/api/convert", {
      method: "POST",
      body: form
    });

    if (!res.ok) {
      throw new Error("Image conversion failed");
    }

    const blob = await res.blob();
    const imgURL = URL.createObjectURL(blob);

    const preview = document.getElementById("preview");
    preview.src = imgURL;
    preview.style.display = "block";
  } catch (err) {
    alert("Server error. Please try again.");
    console.error(err);
  }
}
