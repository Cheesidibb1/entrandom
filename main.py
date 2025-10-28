import cv2
import time

cam = cv2.VideoCapture(0)
if not cam.isOpened():
    raise RuntimeError("Could not open camera")

def imagecapture():
    # take image from camera and outputs it to output/captured_image.png
    try:
        result, image = cam.read()
        if not result:
            print("Failed to capture image")
            raise RuntimeError("Failed to capture image")
        window_name = f"Captured Image"
        cv2.imshow(window_name, image)
        cv2.imwrite(f"output/captured_image.png", image)
        key = cv2.waitKey(1) & 0xFF
        cv2.destroyWindow(window_name)
    finally:
        cam.release()
        cv2.destroyAllWindows()

