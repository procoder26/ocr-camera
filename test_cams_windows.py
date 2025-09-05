import cv2

# Try DirectShow backend first (works best on Windows)
cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)

if not cap.isOpened():
    print("❌ Could not open camera 0 with CAP_DSHOW")
    exit()

print("✅ Camera opened. Press 'q' to quit.")

while True:
    ret, frame = cap.read()
    if not ret:
        print("⚠️ Failed to grab frame")
        break

    cv2.imshow("Camera Test", frame)

    # waitKey(1) keeps window responsive
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
