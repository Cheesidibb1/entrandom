import cv2
import time
import pybase64 as base64
import hashlib
import hmac
import binascii
import os
import secrets

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

# --- Key helpers ----------------------------------------------------------

def load_key_from_env(env_name="ENTRANDOM_KEY"):
    b64 = os.environ.get(env_name)
    if not b64:
        return None
    return base64.b64decode(b64)

def generate_key_bytes(n=32):
    return os.urandom(n)

# --- Hashing helpers ------------------------------------------------------

def hash_file_raw_blake2b(path, digest_size=32):
    h = hashlib.blake2b(digest_size=digest_size)
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.digest()   # raw bytes

def hash_bytes_blake2b(data_bytes, digest_size=32):
    h = hashlib.blake2b(digest_size=digest_size)
    h.update(data_bytes)
    return h.digest()

# --- Combine using keyed blake2b ------------------------------------------

def combine_keyed_blake2b_bytes(a_bytes, b_bytes, key_bytes, digest_size=32):
    if key_bytes is None:
        raise ValueError("Key required for keyed combine (pass key_bytes)")
    h = hashlib.blake2b(digest_size=digest_size, key=key_bytes)
    h.update(b"entrandom-v1:keyed-combine:")              # domain separator
    h.update(len(a_bytes).to_bytes(4, "big") + a_bytes)
    h.update(len(b_bytes).to_bytes(4, "big") + b_bytes)
    return h.hexdigest()

def verify_combined_digest_hex(expected_hex, a_bytes, b_bytes, key_bytes, digest_size=32):
    got = combine_keyed_blake2b_bytes(a_bytes, b_bytes, key_bytes, digest_size)
    return hmac.compare_digest(got, expected_hex)

def createcombinedhash():
    # capture image and show base64 preview
    imagecapture()
    print(base64encode_image("output/captured_image.png"))

    # load secret key from env (base64). If none found, generate an ephemeral key
    key = load_key_from_env("ENTRANDOM_KEY")             # base64 string -> bytes
    if key is None:
        # generate an ephemeral key for demo. In production, set ENTRANDOM_KEY env var.
        key = generate_key_bytes(32)
        print("WARNING: ENTRANDOM_KEY not set — generated ephemeral key for this run.")
        print("If you want persistent keys, generate one and set ENTRANDOM_KEY (base64).")
        print("Ephemeral key (base64):", base64.b64encode(key).decode())

    # compute image digest (raw bytes)
    img_path = "output/captured_image.png"
    img_digest_bytes = hash_file_raw_blake2b(img_path)

    # generate a cryptographic nonce and metadata bytes
    myrand = secrets.token_bytes(16)  # 16 bytes = 128 bits
    meta = b"rnd:" + myrand + b"|ts:" + str(int(time.time())).encode("utf-8")
    meta_digest_bytes = hash_bytes_blake2b(meta)

    # combine using keyed blake2b
    combined_hex = combine_keyed_blake2b_bytes(img_digest_bytes, meta_digest_bytes, key)

    # print results (nonce hex included so you can store/verify later)
    print("nonce (hex):", myrand.hex())
    print("image digest (hex):", img_digest_bytes.hex())
    print("meta digest (hex):", meta_digest_bytes.hex())
    print("combined (hex):", combined_hex)
    return combined_hex, key
