import cv2

# Open the default camera (usually device 0)
cap = cv2.VideoCapture(0)

ret, frame = cap.read()  # Capture one frame
if ret:
    cv2.imwrite("current_frame.jpg", frame)  # Save frame as JPEG

cap.release()  # Release the camera
