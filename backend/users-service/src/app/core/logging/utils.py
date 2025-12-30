import hashlib

def email_hash(email: str) -> str:
    return hashlib.sha256(email.lower().encode()).hexdigest()[:12]
