"""Save codes — encode/decode game state to a portable string.

Allows any player to export their save and load it anywhere (different device,
different browser, or share with a friend) without any backend or login.

Format: zlib-compressed JSON, base64-urlsafe encoded, with a version prefix
and a short checksum so we can detect corrupted/tampered codes.
"""
import json
import base64
import zlib
import hashlib

CODE_VERSION = "PSIM1"


def encode_save(state):
    """Convert a game state dict to a portable save code string."""
    json_str = json.dumps(state, separators=(",", ":"), default=str)
    compressed = zlib.compress(json_str.encode("utf-8"), level=9)
    payload_b64 = base64.urlsafe_b64encode(compressed).decode("ascii")
    checksum = hashlib.sha256(compressed).hexdigest()[:6]
    return f"{CODE_VERSION}.{checksum}.{payload_b64}"


def decode_save(code):
    """Decode a save code string back into a game state dict.

    Returns (state, error). On success error is None.
    """
    code = code.strip().replace("\n", "").replace(" ", "")
    if not code:
        return None, "Empty save code."

    parts = code.split(".", 2)
    if len(parts) != 3:
        return None, "Invalid save code format. Make sure you copied the whole code."

    version, checksum, payload_b64 = parts

    if version != CODE_VERSION:
        return None, f"Save code version mismatch (got {version}, expected {CODE_VERSION}). Save was made on a different game version."

    try:
        compressed = base64.urlsafe_b64decode(payload_b64.encode("ascii"))
    except Exception:
        return None, "Save code is corrupted (base64 decode failed)."

    actual_checksum = hashlib.sha256(compressed).hexdigest()[:6]
    if actual_checksum != checksum:
        return None, "Save code checksum mismatch — code may be corrupted or modified."

    try:
        json_str = zlib.decompress(compressed).decode("utf-8")
        state = json.loads(json_str)
    except Exception as e:
        return None, f"Failed to decode save data: {type(e).__name__}"

    if not isinstance(state, dict) or "national" not in state or "parties" not in state:
        return None, "Decoded data does not look like a valid game state."

    return state, None


def estimate_code_length(state):
    """Estimate how long the resulting save code will be (for UI hints)."""
    code = encode_save(state)
    return len(code)
