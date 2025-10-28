import cv2
import time
import pybase64 as base64

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

def base64encode_image(image_path):
    with open(image_path, "rb") as image_file:
        base64_bytes = base64.b64encode(image_file.read())
        base64_string = base64_bytes.decode("utf-8")
        return base64_string


if __name__ == '__main__':
    imagecapture()
    print(base64encode_image("output/captured_image.png"))