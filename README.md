# Google Lens Quick Capture (Windows)

**Capture any screen region → clipboard → Google Lens, in one keystroke.**

A lightweight Windows tool that eliminates the slow manual workflow of screenshot → save → open Lens → upload.  
It combines a minimal native screenshot selector (Python + Windows API) with a Chrome extension that automatically injects the clipboard image into Google Lens.

---

## Why this is faster

| Manual flow | This tool |
|-------------|-----------|
| Print Screen / Snipping Tool | One hotkey |
| Save file | Automatic |
| Open browser → Lens | Automatic |
| Click upload / drag image | Automatic paste |

Typical end-to-end time: **under 1 second** after selection.

---

## Workflow

1. Press the global hotkey (`Ctrl+Alt+Q`).
2. A semi-transparent fullscreen overlay appears. Drag to select any region.
3. On mouse release:
   - The selected area is encoded as PNG (pure Python + zlib, no external image libraries).
   - The image is placed on the system clipboard using PowerShell.
   - `https://lens.google.com/` is opened in the default browser.
4. The Chrome extension detects the Lens page, reads the clipboard image, and programmatically sets it on the file input (or dispatches a paste event as fallback).

The Python script never uploads anything itself — it only prepares the clipboard and opens the URL. The extension does the rest.

---

## Project Structure

```
google-lens-extension/
├── manifest.json          # MV3 extension config (clipboardRead + host permissions)
├── content.js             # Auto-paste logic on lens.google.com / google.com
├── background.js          # Service worker (minimal)
├── q.pyw                  # Screenshot + clipboard + open Lens (Windows only)
└── windows_install.ps1    # Creates desktop shortcut with Ctrl+Alt+Q
```

---

## Prerequisites

- **Windows 10/11**
- **Python 3.8+** (standard library only — no `pip install` required)
- **Google Chrome** (or Chromium-based browser that supports MV3 extensions)
- **Clipboard access** permission for the extension
- **PowerShell** (pre-installed on Windows)

---

## Installation

### 1. Load the Chrome Extension

1. Open `chrome://extensions/`
2. Enable **Developer mode**
3. Click **Load unpacked**
4. Select this repository folder
5. Confirm the extension appears and has `clipboardRead` + host permissions for `google.com` / `lens.google.com`

### 2. Install the Capture Script (Windows)

```powershell
# If you get an execution-policy error:
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned

# Run the installer (creates a desktop shortcut with Ctrl+Alt+Q)
.\windows_install.ps1
```

After installation, you can use the shortcut or press `Ctrl+Alt+Q` (if the shortcut is placed on the desktop with a hotkey assigned).

---

## Usage

- Press `Ctrl+Alt+Q` (or double-click the generated desktop shortcut).
- Select the region with the mouse. Release to capture.
- Google Lens opens and the image is pasted automatically.

Press `Esc` at any time to cancel the selection overlay.

---

## Technical Notes

### Screenshot path (`q.pyw`)

- Uses pure Windows API (`ctypes` + GDI) for zero-dependency full-screen capture.
- Crops the selected region in memory.
- Writes a valid PNG using only `struct` + `zlib` (no Pillow, no OpenCV).
- Copies the image to the clipboard via a short PowerShell snippet (`System.Windows.Forms.Clipboard`).
- Opens Lens with the standard `webbrowser` module.

### Extension (`content.js`)

- Runs at `document_idle` on `https://www.google.com/*` and `https://lens.google.com/*`.
- Queries `clipboard-read` permission.
- Reads the first image from the clipboard.
- Locates the file input (or falls back to a synthetic `ClipboardEvent`).
- Uses a `MutationObserver` to re-trigger on SPA navigations inside Google.

### Manifest V3

- Minimal permissions: `clipboardRead`, `activeTab`, `storage`.
- Host permissions limited to Google domains.

---

## Troubleshooting

| Symptom | Possible cause | Fix |
|---------|----------------|-----|
| Extension does nothing | Clipboard permission denied | Go to `chrome://extensions` → extension details → allow clipboard access. Reload the page. |
| "No image found in clipboard" | Capture failed or wrong format | Check console of the Lens tab. Ensure the Python script printed "Image copied to clipboard". |
| Python not found | PATH issue | Use full path to `python.exe` in the shortcut or reinstall Python and check "Add Python to PATH". |
| PowerShell execution policy | Restricted policy | `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` |
| Selection overlay does not appear | Python environment issue | Run `python q.pyw` manually in a terminal to see error messages. |
| Lens opens but image is not pasted | Timing / DOM change | The extension retries on URL changes. Try refreshing the Lens page once. |
| Multi-monitor issues | Coordinate system | Current implementation captures the primary virtual screen. Advanced multi-monitor support can be added later. |

---

## Security & Privacy

- No network requests are made by the Python script except opening a local browser tab.
- The image never leaves your machine until *you* interact with Google Lens.
- The extension only runs on Google domains and only reads the clipboard when on those pages.
- Source is fully readable — no obfuscation, no telemetry.

---
**Happy capturing.**
