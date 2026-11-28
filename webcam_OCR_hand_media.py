import cv2

cap = cv2.VideoCapture(0)
mser = cv2.MSER_create()

print("Bright-Room Safe OpenCV OCR Active. Press 'q' to quit.")

while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    
    # 1. Local Contrast Normalization to squash bright room glare/reflections
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    gray = clahe.apply(gray)

    regions, _ = mser.detectRegions(gray)

    for p in regions:
        x, y, w, h = cv2.boundingRect(p)
        
        # Calculate contour area vs bounding box area (Extent) to filter out messy glare blobs
        box_area = w * h
        if box_area == 0:
            continue
            
        # Basic dimension filters for text characters/words
        aspect_ratio = float(w) / h
        if 8 < w < 250 and 10 < h < 60 and 0.2 < aspect_ratio < 6.0:
            
            # Extract ROI to check pixel density (kills bright room reflection false positives)
            roi = gray[y:y+h, x:x+w]
            _, roi_thresh = cv2.threshold(roi, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            white_pixels = cv2.countNonZero(roi_thresh)
            density = white_pixels / float(box_area)

            # Real text has a balanced fill ratio; bright room glare is usually too solid or too sparse
            if 0.15 < density < 0.85:
                cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 1)

    cv2.imshow("Bright-Safe OpenCV OCR", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()