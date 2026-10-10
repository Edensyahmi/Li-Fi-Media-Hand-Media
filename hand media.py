import time
import cv2
import pyautogui

cap = cv2.VideoCapture(0)

print("[*] Lightweight Motion Controller Active!")
print(" -> Move your hand up into the top zone to toggle Play/Pause.")
print(" -> Zero AI bloat, blazing fast, zero CPU usage.")
print(" -> Press [q] to quit.")

ret, prev_frame = cap.read()
if ret:
  prev_frame = cv2.cvtColor(prev_frame, cv2.COLOR_BGR2GRAY)
  prev_frame = cv2.GaussianBlur(prev_frame, (21, 21), 0)

last_trigger_time = 0
triggered = False

while True:
  ret, frame = cap.read()
  if not ret:
    break

  frame = cv2.flip(frame, 1)
  h, w, _ = frame.shape

  gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
  gray = cv2.GaussianBlur(gray, (21, 21), 0)

  # Compute difference between frames
  diff = cv2.absdiff(prev_frame, gray)
  _, thresh = cv2.threshold(diff, 25, 255, cv2.THRESH_BINARY)
  thresh = cv2.dilate(thresh, None, iterations=2)

  contours, _ = cv2.findContours(
      thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
  )

  motion_in_top_zone = False
  for cnt in contours:
    if cv2.contourArea(cnt) > 3000:  # Size filter for hand/arm motion
      x, y, cw, ch = cv2.boundingRect(cnt)
      # Check if movement is in the top half of the screen (hand raised)
      if y < (h // 2):
        motion_in_top_zone = True
        break

  current_time = time.time()

  # Trigger media command with cooldown
  if motion_in_top_zone and not triggered:
    if current_time - last_trigger_time > 2.0:
      last_trigger_time = current_time
      triggered = True
      print("\n[🚀 MOTION TRIGGER] Hand raised! Toggling Media Play/Pause")
      pyautogui.press("playpause")
  elif not motion_in_top_zone:
    triggered = False

  prev_frame = gray.copy()

  # Draw visual divider line for the top zone
  cv2.line(frame, (0, h // 2), (w, h // 2), (0, 255, 255), 2)

  status_text = (
      "STATUS: MOTION IN ZONE!" if motion_in_top_zone else "STATUS: SCANNING..."
  )
  status_color = (0, 255, 0) if motion_in_top_zone else (0, 0, 255)

  cv2.putText(
      frame, status_text, (30, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.7, status_color, 2
  )
  cv2.imshow("Lightweight Motion Controller", frame)

  if (cv2.waitKey(1) & 0xFF) == ord("q"):
    break

cap.release()
cv2.destroyAllWindows()