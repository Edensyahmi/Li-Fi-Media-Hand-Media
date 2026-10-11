# Li-Fi & Hand Media

You can use the flashlight on your phone or your hand gestures to control media playback and the mouse on your PC, with no need for any additional hardware.

![Python](https://img.shields.io/badge/Python-3.8+-3572A5?style=flat-square&logo=python&logoColor=white)
![OpenCV](https://img.shields.io/badge/OpenCV-4.x-e05c00?style=flat-square&logo=opencv&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-2d7a3a?style=flat-square)

---

## Modules

| File | Type | What it does |
|---|---|---|
Li-Fi Media.py | Li-Fi | The quad-LED on the flash phone is directed towards the webcam to play or pause the media.
| hand media.py | Gesture | Raise the hand in the upper frame to play or pause |
lifi mouse.py | Li-Fi Mouse | Aim the flashlight at the webcam → the cursor moves and you can click by holding it down |

---

## How It Works

### Li-Fi Media — Quad-LED Flash Detection
```
webcam → grayscale → sample 4 corners → detect flash blob → playpause
```
**Corner-sampling trick:** Because quad-LEDs result in considerable center bloom, rather than reading the entire frame this method takes samples from the four corners in order to tell the difference between a deliberate flash and ambient room light.

### Hand Media — Frame Diff Motion Detection
```
webcam → frame diff → top-zone check → playpause
```
Without MediaPipe and without loading a model, it uses pure frame differencing—extremely fast and compatible with any hardware.

### Li-Fi Mouse — Brightest-Point Tracking
```
webcam → find brightest spot → EMA smooth → map to screen → dwell-to-click
```
Keep the light down for one second if you want to left-click. Using EMA smoothing eliminates jitter and gives the cursor a more natural movement.

---

## Requirements

- Python 3.8+
- `opencv-python`
- `numpy`
- `pyautogui`
- Any webcam
- Any phone with a flashlight (quad-LED works best)

```bash
pip install opencv-python numpy pyautogui
```

---

## Usage

```bash
# Li-Fi media control
python "Li-Fi Media.py"

# Hand gesture media control
python "hand media.py"

# Li-Fi mouse control
python "lifi mouse.py"
```

You can download All.in.One.zip from [Releases](https://github.com/Edensyahmi/Li-Fi-Media-Hand-Media/releases) — there's no need for Python.

---

## Tips

- **Li-Fi Media:** performs best in a dark or dimmed room since bright rooms cause ambient blocking to be triggered automatically
- **Li-Fi Media:** emit a flash to switch it on and off, with a 1.5-second cooldown period to avoid double triggering
- **Hand Media:** raise arm above frame midline, works in any lighting
- **Li-Fi Mouse:** move the mouse to any corner of the screen to abort (this is a failsafe). Hold it in place for 1 second to click
- **All modules:** press `q` in the webcam window to quit

---

## License

MIT — free for use, modification and distribution.
