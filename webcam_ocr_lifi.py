import time
import cv2
import numpy as np
import pyautogui

# ── Init ──────────────────────────────────────────────────────────────────────
cap = cv2.VideoCapture(0)
mser = cv2.MSER_create()
mser.setMinArea(60)
mser.setMaxArea(2500)

# ── Mode ──────────────────────────────────────────────────────────────────────
# MODE 0 = LIFI  |  MODE 1 = OCR
MODE_LIFI = 0
MODE_OCR  = 1
current_mode = MODE_LIFI
MODE_LABELS  = {MODE_LIFI: "LIFI", MODE_OCR: "OCR"}
MODE_COLORS  = {MODE_LIFI: (0, 255, 180), MODE_OCR: (255, 180, 0)}

# ── State ─────────────────────────────────────────────────────────────────────
last_trigger_time   = 0
last_ocr_time       = 0
ocr_results         = []
OCR_COOLDOWN        = 1.0   # seconds

# Railguard
prev_gray            = None
railguard_active     = False
railguard_until      = 0.0
RAILGUARD_HOLD       = 2.0  # seconds to suppress after trigger
FLICKER_THRESH       = 40   # mean-brightness delta to flag flicker
FAST_BRIGHT_THRESH   = 220  # pixel value threshold for "bright"
FAST_MOTION_AREA     = 800  # min contour area in diff to flag fast object
railguard_reason     = ""

print("[*] Li-Fi / OCR Controller — Mode Switch Edition")
print(" -> [q] quit | [m] switch mode | [o] force OCR scan")
print(f" -> Starting in {MODE_LABELS[current_mode]} mode")


# ── Helpers ───────────────────────────────────────────────────────────────────

def classify_light(gray):
    """
    3-way light classification:
    CEILING LIGHT   : entire frame bright, uniform
    SCREEN AMBIENT  : center bright, edges also somewhat lit
    FLASHLIGHT BEAM : edges dark, center has a HOT bright spot
    """
    h, w = gray.shape
    h_margin, w_margin = h // 4, w // 4

    corners = np.concatenate([
        gray[0:h_margin, 0:w_margin].flatten(),
        gray[0:h_margin, w - w_margin:w].flatten(),
        gray[h - h_margin:h, 0:w_margin].flatten(),
        gray[h - h_margin:h, w - w_margin:w].flatten(),
    ])
    edge_median   = np.median(corners)
    center        = gray[h_margin:h - h_margin, w_margin:w - w_margin]
    center_median = np.median(center)
    center_max    = np.max(center)

    if edge_median > 80:
        return "CEILING LIGHT", (0, 165, 255), False
    elif center_median > 60 and edge_median > 30:
        return "SCREEN AMBIENT", (255, 255, 0), False
    else:
        _, thresh_beam = cv2.threshold(gray, 220, 255, cv2.THRESH_BINARY)
        contours, _ = cv2.findContours(
            thresh_beam, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
        )
        valid_beam = (
            any(15 < cv2.contourArea(c) < 10000 for c in contours)
            and center_max > 235
        )
        if valid_beam:
            return "FLASHLIGHT / LED BEAM", (0, 255, 0), True
        else:
            return "SCANNING...", (0, 0, 255), False


def detect_text_regions(gray):
    """MSER + contour filtering → list of (x, y, w, h) text bounding boxes."""
    blurred  = cv2.GaussianBlur(gray, (3, 3), 0)
    regions, _ = mser.detectRegions(blurred)

    boxes = []
    for p in regions:
        x, y, w, h = cv2.boundingRect(p)
        aspect = float(w) / h if h != 0 else 0
        if 5 < w < 400 and 8 < h < 100 and 0.1 < aspect < 12.0:
            boxes.append((x, y, w, h))

    if not boxes:
        return []

    boxes.sort(key=lambda b: b[2] * b[3], reverse=True)
    merged = []
    for box in boxes:
        x, y, w, h = box
        keep = True
        for mx, my, mw, mh in merged:
            ix = max(x, mx);  iy = max(y, my)
            iw = min(x + w, mx + mw) - ix
            ih = min(y + h, my + mh) - iy
            if iw > 0 and ih > 0:
                if (iw * ih) / float(w * h) > 0.4:
                    keep = False
                    break
        if keep:
            merged.append(box)
    return merged


def check_railguard(gray, prev):
    """
    Returns (triggered: bool, reason: str).
    Checks:
      1. Flicker  — sudden mean-brightness jump between frames
      2. Fast bright moving object — large bright contour in frame diff
    """
    if prev is None:
        return False, ""

    # 1. Flicker
    delta_mean = abs(float(np.mean(gray)) - float(np.mean(prev)))
    if delta_mean > FLICKER_THRESH:
        return True, "FLICKER"

    # 2. Fast bright moving object
    diff = cv2.absdiff(gray, prev)
    _, bright_mask = cv2.threshold(gray, FAST_BRIGHT_THRESH, 255, cv2.THRESH_BINARY)
    moving_bright  = cv2.bitwise_and(diff, diff, mask=bright_mask)
    _, motion_thresh = cv2.threshold(moving_bright, 25, 255, cv2.THRESH_BINARY)
    contours, _ = cv2.findContours(
        motion_thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
    )
    if any(cv2.contourArea(c) > FAST_MOTION_AREA for c in contours):
        return True, "FAST BRIGHT OBJECT"

    return False, ""


# ── Main loop ─────────────────────────────────────────────────────────────────
while True:
    ret, frame = cap.read()
    if not ret:
        break

    gray         = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    current_time = time.time()

    # ── RAILGUARD (always runs) ───────────────────────────────────────────────
    triggered, reason = check_railguard(gray, prev_gray)
    if triggered and not railguard_active:
        railguard_active = True
        railguard_until  = current_time + RAILGUARD_HOLD
        railguard_reason = reason
        print(f"[⚠ RAILGUARD] {reason} detected — suppressing for {RAILGUARD_HOLD}s")

    if railguard_active and current_time > railguard_until:
        railguard_active = False
        railguard_reason = ""

    prev_gray = gray.copy()

    # ── MODE: LIFI ────────────────────────────────────────────────────────────
    light_label = "---"
    light_color = (100, 100, 100)
    valid_beam  = False

    if current_mode == MODE_LIFI:
        light_label, light_color, valid_beam = classify_light(gray)

        if valid_beam and not railguard_active:
            if current_time - last_trigger_time > 1.5:
                last_trigger_time = current_time
                print("\n[⚡ LI-Fi LOCK] Beam confirmed! Toggling Play/Pause")
                pyautogui.press("playpause")

    # ── MODE: OCR ─────────────────────────────────────────────────────────────
    if current_mode == MODE_OCR and not railguard_active:
        if current_time - last_ocr_time > OCR_COOLDOWN:
            last_ocr_time = current_time
            ocr_results   = detect_text_regions(gray)
        for (x, y, w, h) in ocr_results:
            cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 0, 0), 2)
    elif current_mode == MODE_OCR and railguard_active:
        # skip OCR this cycle but keep old boxes visible (faded)
        for (x, y, w, h) in ocr_results:
            cv2.rectangle(frame, (x, y), (x + w, y + h), (100, 0, 0), 1)

    # ── HUD ───────────────────────────────────────────────────────────────────
    mode_label = MODE_LABELS[current_mode]
    mode_color = MODE_COLORS[current_mode]

    rg_text  = f"RAILGUARD: !! {railguard_reason}" if railguard_active else "RAILGUARD: SAFE"
    rg_color = (0, 60, 255) if railguard_active else (0, 220, 100)

    if current_mode == MODE_LIFI:
        hud_lines = [
            (f"MODE: {mode_label}  [m] to switch", mode_color),
            (f"LIGHT: {light_label}", light_color),
            (rg_text, rg_color),
        ]
    else:
        hud_lines = [
            (f"MODE: {mode_label}  [m] to switch | [o] force scan", mode_color),
            (f"REGIONS: {len(ocr_results)} text boxes", (200, 200, 200)),
            (rg_text, rg_color),
        ]

    for i, (txt, col) in enumerate(hud_lines):
        cv2.putText(frame, txt, (20, 35 + i * 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, col, 2)

    cv2.imshow("Li-Fi / OCR Controller", frame)

    # ── Keys ──────────────────────────────────────────────────────────────────
    key = cv2.waitKey(1) & 0xFF
    if key == ord("q"):
        break
    elif key == ord("m"):
        current_mode = MODE_OCR if current_mode == MODE_LIFI else MODE_LIFI
        ocr_results  = []
        print(f"[MODE] Switched to {MODE_LABELS[current_mode]}")
    elif key == ord("o") and current_mode == MODE_OCR:
        last_ocr_time = 0

cap.release()
cv2.destroyAllWindows()
