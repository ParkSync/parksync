import cv2
from ultralytics import YOLO
from paddleocr import PaddleOCR
import numpy as np
from server import manage_numberplate_db
import time

# Initialize PaddleOCR
ocr = PaddleOCR()

# Load video and YOLO model
cap = cv2.VideoCapture('vehicle_passby.mp4')
model = YOLO("best_float32.tflite")

# Load class names
with open("coco1.txt", "r") as f:
    class_names = f.read().splitlines()

# Function to perform OCR
def perform_ocr(image_array):
    if image_array is None or image_array.size == 0:
        return ""

    results = ocr.ocr(image_array, rec=True)
    detected_text = []

    if results and results[0] is not None:
        for result in results[0]:
            text = result[1][0]
            detected_text.append(text)

    return ''.join(detected_text)

# Mouse callback for debugging
def RGB(event, x, y, flags, param):
    if event == cv2.EVENT_MOUSEMOVE:
        print(f"Mouse Position: {x}, {y}")

cv2.namedWindow('ANPR')
cv2.setMouseCallback('ANPR', RGB)

# Detection region
area = [(5, 180), (3, 249), (984, 237), (950, 168)]
counter = []

# Initialize status message and timing
status_message = "Standing By"
message_display_time = 0  # Time when the message was last updated
display_duration = 2  # Duration to display the message in seconds

# Define colors in BGR format
colors = {
    "Standing By": (0, 255, 255),  # Yellow
    "Gateway Open!": (0, 255, 0),  # Green
    "Unknown Vehicle!": (0, 0, 255)  # Red
}

while True:
    ret, frame = cap.read()
    if not ret:
        break

    frame = cv2.resize(frame, (1020, 500))
    results = model.track(frame, persist=True, imgsz=256)

    # Check if the display duration has passed
    if time.time() - message_display_time > display_duration:
        # Default message
        status_message = "Standing By"

    # Process detections
    if results[0].boxes is not None and results[0].boxes.id is not None:
        boxes = results[0].boxes.xyxy.int().cpu().tolist()
        class_ids = results[0].boxes.cls.int().cpu().tolist()
        track_ids = results[0].boxes.id.int().cpu().tolist()

        for box, class_id, track_id in zip(boxes, class_ids, track_ids):
            c = class_names[class_id]
            x1, y1, x2, y2 = box
            cx, cy = (x1 + x2) // 2, (y1 + y2) // 2

            result = cv2.pointPolygonTest(np.array(area, np.int32), (cx, cy), False)
            if result >= 0 and track_id not in counter:
                counter.append(track_id)
                crop = frame[y1:y2, x1:x2]
                crop = cv2.resize(crop, (120, 70))

                text = perform_ocr(crop)
                text = text.replace('(', '').replace(')', '').replace(',', '').replace(']', '').replace('-', ' ')
                new_status_message = manage_numberplate_db(text)

                # Update the status message and reset the timer
                status_message = new_status_message
                message_display_time = time.time()

    # Display status message on video
    color = colors.get(status_message, (255, 255, 255))  # Default to white if status not found
    font = cv2.FONT_HERSHEY_SIMPLEX
    font_scale = 1
    thickness = 2
    text_size = cv2.getTextSize(status_message, font, font_scale, thickness)[0]
    text_x = frame.shape[1] - text_size[0] - 10
    text_y = frame.shape[0] - 10
    cv2.putText(frame, status_message, (text_x, text_y), font, font_scale, color, thickness)
    print(status_message)
    cv2.polylines(frame, [np.array(area, np.int32)], True, (255, 0, 0), 2)
    cv2.imshow("ANPR", frame)

    if cv2.waitKey(100) & 0xFF == 27:  # Press 'Esc' to exit
        break

cap.release()
cv2.destroyAllWindows()
