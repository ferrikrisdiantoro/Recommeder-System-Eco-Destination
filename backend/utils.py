import re
import bcrypt

def parse_price_idr(s):
    """Parse string harga IDR seperti 'Rp25,000', '10k', '1 jt' → float rupiah."""
    if s is None:
        return 0.0
    t = str(s).strip().lower()
    if t in {"", "-", "n/a", "na"} or any(x in t for x in ["gratis", "free", "donasi"]):
        return 0.0

    mult = 1
    if ("jt" in t) or ("juta" in t):
        mult = 1_000_000
    elif re.search(r"\b(k|rb|ribu)\b", t):
        mult = 1_000

    digits = re.sub(r"[^0-9]", "", t)
    return float(int(digits) * mult) if digits else 0.0

def hash_password(pw: str) -> bytes:
    return bcrypt.hashpw(pw.encode("utf-8"), bcrypt.gensalt())

def check_password(pw: str, hashed: bytes) -> bool:
    try:
        return bcrypt.checkpw(pw.encode("utf-8"), hashed)
    except Exception:
        return False
