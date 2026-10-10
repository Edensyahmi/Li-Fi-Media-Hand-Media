import time
import cv2
import numpy as np
import pyautogui

# Safety configuration
pyautogui.FAILSAFE = True  # Move mouse to any corner to abort

# Initialize webcam (0 is usually the default camera)
cap = cv2.VideoCapture(0)

if not cap.isOpened():
  print("Error: Could not open webcam.")
  exit()

# Get screen dimensions for coordinate mapping
screen_width, screen_height = pyautogui.size()

# Dwell click parameters
DWELL_TIME = 1.0  # Seconds required to trigger a click
DWELL_RADIUS = 25  # Max pixel movement allowed during dwell
dwell_start_time = None
dwell_center = None
has_clicked = (
    False  # Prevents continuous looping while holding light in one spot
)

# Smoothing parameters (EMA)
alpha = 0.3
smooth_x, smooth_y = 0, 0
first_frame = True

print("Li-Fi Mouse Running. Press 'q' to quit.")

while True:
  ret, frame = cap.read()
  if not ret:
    print("Error: Failed to grab frame.")
    break

  # Flip frame horizontally for a natural mirror view
  frame = cv2.flip(frame, 1)
  h, w, _ = frame.shape

  # Convert to grayscale and blur to remove high-frequency noise
  gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
  blurred = cv2.GaussianBlur(gray, (11, 11), 0)

  # Find the brightest spot (the phone flashlight)
  min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(blurred)

  # Threshold to ensure we actually have a bright light source
  if max_val > 200:
    cx, cy = max_loc

    # Map webcam coordinates to screen coordinates
    target_x = np.interp(cx, (0, w), (0, screen_width))
    target_y = np.interp(cy, (0, h), (0, screen_height))

    # Apply exponential moving average (EMA) for smooth cursor gliding
    if first_frame:
      smooth_x, smooth_y = target_x, target_y
      first_frame = False
    else:
      smooth_x = smooth_x * (1 - alpha) + target_x * alpha
      smooth_y = smooth_y * (1 - alpha) + target_y * alpha

    # Move cursor
    pyautogui.moveTo(int(smooth_x), int(smooth_y))

    # Dwell-to-click logic
    current_time = time.time()
    if dwell_center is None:
      dwell_center = (cx, cy)
      dwell_start_time = current_time
      has_clicked = False
    else:
      # Check how far the light has moved from the dwell center
      distance = np.hypot(cx - dwell_center[0], cy - dwell_center[1])

      if distance < DWELL_RADIUS:
        # Light is holding still
        if not has_clicked and (current_time - dwell_start_time >= DWELL_TIME):
          pyautogui.click()
          has_clicked = True  # Lock until light moves away
      else:
        # Light moved, reset dwell tracking and click lock
        dwell_center = (cx, cy)
        dwell_start_time = current_time
        has_clicked = False

    # Draw tracking indicator on feed
    cv2.circle(frame, (cx, cy), 15, (0, 255, 0), 2)
    cv2.circle(frame, (cx, cy), 3, (0, 0, 255), -1)
  else:
    # Reset dwell state if light is lost
    dwell_center = None
    dwell_start_time = None
    has_clicked = False

  # Display feed
  cv2.imshow("Li-Fi Mouse Tracker", frame)

  # Exit on pressing 'q'
  if cv2.waitKey(1) & 0xFF == ord("q"):
    break

cap.release()
cv2.destroyAllWindows()