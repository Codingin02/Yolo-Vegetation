(function () {
  const image = document.getElementById("annotatedImage");
  if (!image) return;
  image.addEventListener("error", () => {
    const parent = image.parentElement;
    if (!parent) return;
    parent.innerHTML = '<div class="image-placeholder">ANNOTATION_NOT_READY</div>';
  });
})();
