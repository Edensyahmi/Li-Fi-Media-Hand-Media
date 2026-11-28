# Li-Fi Media Hand Media 🔦

A Python webcam controller that uses Li-Fi (light-based communication) and computer vision to detect light signals and text regions in real time — no hardware buttons needed.

## Files

| File | Description |
|------|-------------|
| `webcam_ocr_lifi.py` | Combined mode — LIFI + OCR with mode switch and safety railguard |
| `Li-Fi_Media.py` | Standalone Li-Fi controller — quad-LED proof corner-sampling beam detection |
| `webcam_OCR_hand_media.py` | Standalone OCR — bright-room safe MSER text region detector |

---

## `webcam_ocr_lifi.py` — Combined LIFI + OCR

The main file. Runs both modes separately with a toggle.

### Modes
Press `[M]` to switch — they don't run simultaneously.

| Mode | What it does |
|------|-------------|
| **LIFI** | Detects flashlight/LED beam and toggles play/pause |
| **OCR** | Detects text regions on screen using MSER + OpenCV |

### Safety Railguard
Runs in both modes always. Suppresses actions for 2 seconds when:
- ⚡ Light flicker detected (sudden brightness jump between frames)
- 🔆 Fast bright moving object detected (frame differencing)

HUD shows `RAILGUARD: SAFE` or `RAILGUARD: !! FLICKER`

### Controls
| Key | Action |
|-----|--------|
| `M` | Switch between LIFI / OCR mode |
| `O` | Force OCR scan (OCR mode only) |
| `Q` | Quit |

---

## `Li-Fi_Media.py` — Quad-LED Proof Li-Fi Controller

Standalone Li-Fi beam detector optimized for quad-LED setups where center blooming is an issue. Uses **corner sampling** instead of whole-frame brightness to avoid false positives from ambient room light.

- Samples 4 corner regions to detect true room light vs beam
- Tolerates massive center blooming from quad-LEDs
- Triggers `play/pause` media key on valid beam detection (1.5s cooldown)

---

## `webcam_OCR_hand_media.py` — Bright-Room Safe OCR

Standalone MSER text region detector built for bright environments.

- Uses CLAHE (Contrast Limited Adaptive Histogram Equalization) to normalize glare
- Pixel density filtering to kill bright-room reflection false positives
- Draws green boxes around detected text-like regions

---

## Requirements

```bash
pip install opencv-python numpy pyautogui
```

## Run

```bash
# Combined mode (recommended)
python webcam_ocr_lifi.py

# Standalone Li-Fi only
python Li-Fi_Media.py

# Standalone OCR only
python webcam_OCR_hand_media.py
```

## License

MIT — see [LICENSE](LICENSE)
