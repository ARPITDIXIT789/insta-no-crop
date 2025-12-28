let busy = false;

async function upload() {
  if (busy) return;

  const file = document.getElementById("file").files[0];
  if (!file) {
    alert("Select an image first");
    return;
  }

  busy = true;
  const btn = document.querySelector("button");
  btn.innerText = "Processing...";
  btn.disabled = true;

  const form = new FormData();
  form.append("file", file);

  try {
    const res = await fetch("/convert", {
      method: "POST",
      body: form
    });

    if (!res.ok) throw new Error();

    const blob = await res.blob();
    const url = URL.createObjectURL(blob);

    const img = document.getElementById("preview");
    const dl = document.getElementById("downloadBtn");

    img.src = url;
    img.style.display = "block";

    dl.href = url;
    dl.style.display = "inline-block";
  } catch {
    alert("Conversion failed");
  }

  btn.innerText = "Convert";
  btn.disabled = false;
  busy = false;
}
