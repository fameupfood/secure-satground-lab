import hmac
import hashlib


def verify_hmac(body: bytes, secret: str, received_sig: str) -> bool:
    mac = hmac.new(secret.encode("utf-8"), body, hashlib.sha256)
    expected = mac.hexdigest()
    # constant-time comparison
    return hmac.compare_digest(expected, received_sig or "")
