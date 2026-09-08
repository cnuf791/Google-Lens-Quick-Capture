async function pasteLastImageFromClipboard() {
  try {
    const permissionStatus = await navigator.permissions.query({ name: "clipboard-read" });
    if (permissionStatus.state === "denied") {
      console.warn("Clipboard read permission denied");
      return;
    }
    
    const clipboardItems = await navigator.clipboard.read();
    let imageBlob = null;
    
    for (const item of clipboardItems) {
      const imageTypes = item.types.filter(type => type.startsWith("image/"));
      if (imageTypes.length > 0) {
        imageBlob = await item.getType(imageTypes[0]);
        break;
      }
    }
    
    if (!imageBlob) {
      console.log("No image found in clipboard");
      return;
    }
    let fileInput = document.querySelector('input[type="file"]');
    if (!fileInput) {
      const pasteEvent = new ClipboardEvent('paste', {
        bubbles: true,
        cancelable: true
      });
      document.activeElement?.dispatchEvent(pasteEvent);
      document.body.dispatchEvent(pasteEvent);
      console.log("Dispatched paste event (no file input found)");
      return;
    }
    
    const file = new File([imageBlob], "clipboard-image.png", { type: imageBlob.type });
    const dataTransfer = new DataTransfer();
    dataTransfer.items.add(file);
    fileInput.files = dataTransfer.files;
    fileInput.dispatchEvent(new Event('change', { bubbles: true }));
    
    console.log("Image successfully pasted to file input");
    
  } catch (err) {
    console.error("Failed to read clipboard or paste:", err);
  }
}

function isGooglePage() {
  return window.location.hostname.includes('google.com');
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', () => {
    setTimeout(() => {
      if (isGooglePage()) pasteLastImageFromClipboard();
    }, 100);
  });
} else {
  setTimeout(() => {
    if (isGooglePage()) pasteLastImageFromClipboard();
  }, 100);
}

let lastUrl = location.href;
new MutationObserver(() => {
  const url = location.href;
  if (url !== lastUrl && isGooglePage()) {
    lastUrl = url;
    setTimeout(() => {
      pasteLastImageFromClipboard();
    }, 100);
  }
}).observe(document, { subtree: true, childList: true });