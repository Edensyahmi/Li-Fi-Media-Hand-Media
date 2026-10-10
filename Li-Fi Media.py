import time
import cv2
import numpy as np
import pyautogui

cap = cv2.VideoCapture(0)

print("[*] Quad-LED Proof Li-Fi Controller Active!")
print(
    " -> Uses corner-sampling to ignore blinding central sensor bloom from"
    " quad-LEDs."
)
print(" -> Press [q] to quit.")

last_trigger_time = 0

while True:
  ret, frame = cap.read()
  if not ret:
    break

  gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
  h, w = gray.shape

  # --- FIX: SAMPLE CORNERS INSTEAD OF WHOLE FRAME ---
  # Quad-LEDs cause massive center blooming, but room corners stay dark in a dark room.
  h_margin, w_margin = h // 4, w // 4
  corners = np.concatenate([
      gray[0:h_margin, 0:w_margin].flatten(),  # Top-left
      gray[0:h_margin, w - w_margin : w].flatten(),  # Top-right
      gray[h - h_margin : h, 0:w_margin].flatten(),  # Bottom-left
      gray[h - h_margin : h, w - w_margin : w].flatten(),  # Bottom-right
  ])
  edge_median = np.median(corners)

  # If the outer room corners are bright, room lights are truly on!
  if edge_median > 55:
    cv2.putText(
        frame,
        "STATUS: ROOM LIGHTS ON (Ambient Blocked)",
        (20, 40),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.5,
        (0, 165, 255),
        2,
    )
    cv2.imshow("Quad-LED Proof Li-Fi Controller", frame)
    if (cv2.waitKey(1) & 0xFF) == ord("q"):
      break
    continue

  # --- BLINDING BEAM DETECTION ---
  max_val = np.max(gray)
  _, thresh = cv2.threshold(gray, 220, 255, cv2.THRESH_BINARY)
  contours, _ = cv2.findContours(
      thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
  )

  valid_beam = False
  current_time = time.time()

  for cnt in contours:
    area = cv2.contourArea(cnt)
    # Massive area tolerance window to swallow quad-LED blooming explosion
    if 15 < area < 10000:
      if max_val > 235:
        valid_beam = True
        break

  # Trigger media toggle with cooldown
  if valid_beam and (current_time - last_trigger_time > 1.5):
    last_trigger_time = current_time
    print(
        "\n[⚡ QUAD-LED LI-Fi LOCK] Blinding flash verified! Toggling Media"
        " Play/Pause"
    )
    pyautogui.press("playpause")

  # HUD Display
  status_color = (0, 255, 0) if valid_beam else (0, 0, 255)
  status_text = (
      "STATUS: QUAD-LED BEAM LOCKED"
      if valid_beam
      else "STATUS: SCANNING FOR FLASH..."
  )

  cv2.putText(
      frame,
      status_text,
      (30, 40),
      cv2.FONT_HERSHEY_SIMPLEX,
      0.6,
      status_color,
      2,
  )
  cv2.imshow("Quad-LED Proof Li-Fi Controller", frame)

  if (cv2.waitKey(1) & 0xFF) == ord("q"):
    break

cap.release()
cv2.destroyAllWindows()