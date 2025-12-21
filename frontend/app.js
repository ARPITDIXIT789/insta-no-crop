async function upload() {
  const file = document.getElementById("file").files[0];
  const form = new FormData();
  form.append("file", file);

  const res = await fetch("http://localhost:8000/convert", {
    method: "POST",
    body: form
  });

  const blob = await res.blob();
  document.getElementById("preview").src = URL.createObjectURL(blob);
}
