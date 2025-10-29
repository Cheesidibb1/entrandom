# entrandom
## Greetings!
Hello there! this is Entrandom, a project aiming toward a *near* perfect CSPRNG

This is based off of Cloudflare's lava lamps, now making it open source.

This is also a little side project so we will see where we go with it!

I decided to name this project *Entrandom* because of entropy, the lack of order or predictability

This is a small utility to capture an image from a webcam, produce a digest of the image, generate a short cryptographic nonce, and produce a secure combined digest using keyed BLAKE2b.

This README explains how to generate and store a key, how to run `main.py`, and how to verify a previously-produced combined digest.

## Requirements

- Python 3.8+ (tested with 3.9)
- Packages: `opencv-python`, `pybase64` (these may be listed in `requirements.txt`)

Install dependencies (example):

```powershell
python -m pip install -r requirements.txt
```

If you only need the crypto helpers and not camera capture, Python stdlib's `hashlib` is sufficient.

## Keyed combine (recommended)

The project uses keyed BLAKE2b (via `hashlib.blake2b(key=...)`) to combine two digests securely and efficiently. The process is:

1. Hash the image bytes with BLAKE2b (raw digest bytes).
2. Generate a nonce and pack metadata, hash that with BLAKE2b.
3. Use a secret key (32 bytes) and compute keyed BLAKE2b over a canonical blob containing both digests.

Keyed BLAKE2b provides a MAC-like construction (authenticity + integrity) and is very fast.

### Generating and storing a key

Generate a base64-encoded key once and store it in an environment variable `ENTRANDOM_KEY` (or your secret store). Example (PowerShell):

```powershell
python -c "import os,base64; print(base64.b64encode(os.urandom(32)).decode())"

#$env:ENTRANDOM_KEY = 'PASTE_BASE64_KEY_HERE'            # current session
setx ENTRANDOM_KEY 'PASTE_BASE64_KEY_HERE'              # user-level (restart session)
```

Do NOT commit the key to the repo. Use a secrets manager in production.

### Run `main.py`

The `main.py` script will:

- Capture an image to `output/captured_image.png` using the default camera.
- Generate a nonce, compute image and metadata digests, and combine them with the key.
- Print the nonce (hex), image digest (hex), meta digest (hex), and the final combined hex digest.

Run it from PowerShell (will open your webcam briefly):

```powershell
& python main.py
```

If `ENTRANDOM_KEY` is not set the script will generate an ephemeral key and print it with a warning — ephemeral keys are not usable for later verification unless you record them.

## Verification

To verify a previously-produced combined digest, you must have:

- The same secret key that was used to produce the combined digest.
- The original image file (or the original image digest saved earlier).
- The nonce (hex) and timestamp printed at creation (so you can reconstruct the metadata bytes).

Use the `verify_combined_digest_hex` helper in `main.py` or recompute the same steps:

```python
from main import load_key_from_env, hash_file_raw_blake2b, hash_bytes_blake2b, verify_combined_digest_hex
key = load_key_from_env('ENTRANDOM_KEY')
img_digest = hash_file_raw_blake2b('output/captured_image.png')
nonce = bytes.fromhex('PASTE_NONCE_HEX')
meta = b'rnd:' + nonce + b'|ts:' + b'PASTE_TS'
meta_digest = hash_bytes_blake2b(meta)
ok = verify_combined_digest_hex('PASTE_COMBINED_HEX', img_digest, meta_digest, key)
print('verified:', ok)
```

Use `hmac.compare_digest` (already handled by the helper) for constant-time comparison.

## Helper functions in `main.py`

Primary helpers you may use directly:

- `load_key_from_env(env_name='ENTRANDOM_KEY')` — returns raw key bytes (base64 env) or `None`.
- `generate_key_bytes(n=32)` — generate secure random key bytes.
- `hash_file_raw_blake2b(path, digest_size=32)` — returns raw digest bytes for a file.
- `hash_bytes_blake2b(data_bytes, digest_size=32)` — return raw digest bytes for byte input.
- `combine_keyed_blake2b_bytes(a_bytes, b_bytes, key_bytes, digest_size=32)` — returns final combined hex digest.
- `verify_combined_digest_hex(expected_hex, a_bytes, b_bytes, key_bytes)` — verify combined digest.

## Security notes

- Store keys in a secure secrets manager. Avoid hardcoding. Rotate keys regularly.
- Hash raw bytes of images (not base64 text) to avoid canonicalization pitfalls.
- Include domain separation and length-prefixing (the code does this) to avoid ambiguity.

## Troubleshooting

- If the camera doesn't open, ensure your OS allows camera access and the correct device index is used.
- If verification fails, ensure you used the same key, same nonce/timestamp, and the exact same image bytes (no recompression changes).
