(function () {
  const image = document.getElementById("annotatedImage");
  if (!image) return;
  image.addEventListener("error", () => {
    const parent = image.parentElement;
    if (!parent) return;
    parent.innerHTML = '<div class="image-placeholder">ANNOTATED_IMAGE_NOT_AVAILABLE</div>';
  });
})();
