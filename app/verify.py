from nacl.exceptions import BadSignatureError
from nacl.signing import VerifyKey


def verify_signature(body: bytes, signature: str, timestamp: str, public_key: str) -> bool:
    if not signature or not timestamp or not public_key:
        return False
    try:
        vk = VerifyKey(bytes.fromhex(public_key))
        vk.verify(timestamp.encode() + body, bytes.fromhex(signature))
        return True
    except (BadSignatureError, ValueError):
        return False
