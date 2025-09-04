import os
import re
import pandas as pd
import bcrypt
from pandas.api.types import is_numeric_dtype
from .models import Place

# ---------- Price helpers ----------
def parse_price_idr(s):
    """Parse string harga IDR seperti 'Rp25.000', '10k', '1 jt' → float rupiah."""
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

def format_price_idr(n: float) -> str:
    """Format angka (rupiah) menjadi 'Rp1.234.567' tanpa desimal."""
    try:
        val = int(round(float(n)))
        s = f"{val:,}".replace(",", ".")
        return f"Rp{s}"
    except Exception:
        return ""

def display_price(price_str: str | None, price_num: float | None) -> str:
    """Gunakan price_str jika ada; kalau kosong dan price_num>0 → format; else '-'."""
    if price_str and str(price_str).strip():
        return str(price_str).strip()
    if price_num and float(price_num) > 0:
        f = format_price_idr(price_num)
        return f if f else "-"
    return "-"

# ---------- Auth helpers ----------
def hash_password(pw: str) -> bytes:
    return bcrypt.hashpw(pw.encode("utf-8"), bcrypt.gensalt())

def check_password(pw: str, hashed: bytes) -> bool:
    try:
        return bcrypt.checkpw(pw.encode("utf-8"), hashed)
    except Exception:
        return False

# ---------- Serializers ----------
def place_to_dict(p: Place, detail: bool = False):
    d = {
        "place_id": p.id,
        "place_name": p.place_name,
        "city": p.city,
        "category": p.category,
        "price": display_price(p.price_str, p.price_num),
        "rating": p.rating_avg or 0.0,
        "image": p.image,
    }
    if detail:
        d.update({
            "description": p.place_description,
            "address": p.address,
            "gallery1": p.gallery1,
            "gallery2": p.gallery2,
            "gallery3": p.gallery3,
            "map_url": p.map_url,
        })
    return d

# ---------- Sumber CSV ----------
def _find_places_csv():
    """
    Urutan prioritas:
    1) models/place_clean.csv           (harga numerik)
    2) models/cbf/places_clean.csv      (artefak CBF)
    3) data/eco_place.csv               (raw string 'Rp…')
    """
    base = os.path.dirname(__file__)
    candidates = [
        os.path.join(base, "models", "place_clean.csv"),
        os.path.join(base, "models", "cbf", "places_clean.csv"),
        os.path.join(base, "data",  "eco_place.csv"),
    ]
    for p in candidates:
        if os.path.exists(p):
            return p
    return None

def _resolve_price_columns(df: pd.DataFrame):
    """
    Kembalikan (price_str_series, price_num_series) yang siap dipakai ke DB.
    - Jika ada kolom numerik (price_num/int) → itu jadi price_num
    - price_str diambil dari kolom string harga kalau ada; kalau kosong → format dari price_num
    - Khusus sumber eco_place.csv: 'price' adalah string 'Rp…' → price_str=asli, price_num=parse
    """
    # deteksi sumber eco_place.csv (cirinya ada kolom 'price' bertipe string + header spesifik lain)
    looks_like_eco = "price" in df.columns and not is_numeric_dtype(df["price"])

    # kandidat kolom
    str_candidates = [c for c in df.columns if c.lower() in {"price", "harga", "ticket_price", "price_idr", "price_str"}]
    num_candidates = [c for c in df.columns if c.lower() in {"price_num", "harga_num", "price_int", "price_integer"}]

    # default
    price_str = pd.Series([""] * len(df), dtype="object")
    price_num = pd.Series([0.0] * len(df), dtype="float64")

    # kalau eco_place.csv → pakai langsung
    if looks_like_eco:
        s = df["price"].fillna("").astype(str)
        price_str = s
        price_num = s.apply(parse_price_idr)
        return price_str, price_num

    # kalau bukan eco, cari numeric lebih dulu
    used_num = False
    for c in num_candidates:
        if c in df.columns and is_numeric_dtype(df[c]):
            price_num = pd.to_numeric(df[c], errors="coerce").fillna(0.0)
            used_num = True
            break

    if not used_num:
        # bisa jadi ada kolom 'price' yang numeric
        for c in str_candidates:
            if c in df.columns and is_numeric_dtype(df[c]):
                price_num = pd.to_numeric(df[c], errors="coerce").fillna(0.0)
                used_num = True
                break

    # bangun price_str dari kolom string harga kalau ada
    chosen_str = None
    for c in str_candidates:
        if c in df.columns and not is_numeric_dtype(df[c]):
            chosen_str = c
            break
    if chosen_str:
        price_str = df[chosen_str].fillna("").astype(str)

    # fallback: format dari price_num
    price_str = price_str.where(price_str.str.strip() != "",
                                price_num.apply(lambda x: format_price_idr(x) if float(x) > 0 else ""))

    return price_str.astype(str), pd.to_numeric(price_num, errors="coerce").fillna(0.0)

def seed_places_if_empty(db_):
    """Seed tabel places sekali dari CSV yang tersedia (lihat _find_places_csv)."""
    if Place.query.first():
        return

    csv_path = _find_places_csv()
    if not csv_path:
        print("[seed] Tidak menemukan CSV (models/place_clean.csv | models/cbf/places_clean.csv | data/eco_place.csv). Skip.")
        return

    print(f"[seed] Memakai sumber: {csv_path}")
    df = pd.read_csv(csv_path)

    # Normalisasi nama kolom
    colmap = {
        "place_id": "id",
        "id": "id",
        "place_name": "place_name",
        "place_description": "place_description",
        "category": "category",
        "city": "city",
        "description_location": "address",
        "address": "address",
        "place_img": "image",
        "image": "image",
        "gallery_photo_img1": "gallery1",
        "gallery_photo_img2": "gallery2",
        "gallery_photo_img3": "gallery3",
        "gallery1": "gallery1",
        "gallery2": "gallery2",
        "gallery3": "gallery3",
        "place_map": "map_url",
        "map_url": "map_url",
        "rating": "rating",
        "rating_avg": "rating_avg",
        # harga akan diselesaikan via _resolve_price_columns
        "price": "price",
        "harga": "price",
        "ticket_price": "price",
        "price_idr": "price",
        "price_str": "price_str",
        "price_num": "price_num",
    }
    for c in list(df.columns):
        if c in colmap:
            df = df.rename(columns={c: colmap[c]})

    # id wajib ada
    if "id" not in df.columns:
        if "Unnamed: 0" in df.columns:
            df = df.rename(columns={"Unnamed: 0": "id"})
        else:
            raise KeyError("CSV tidak memiliki kolom 'id' / 'place_id'.")

    df["id"] = pd.to_numeric(df["id"], errors="coerce").astype("Int64")
    df = df.dropna(subset=["id"]).astype({"id": int})

    # rating_avg
    if "rating_avg" not in df.columns and "rating" in df.columns:
        df["rating_avg"] = pd.to_numeric(df["rating"], errors="coerce").fillna(0.0)
    else:
        df["rating_avg"] = pd.to_numeric(df.get("rating_avg", 0.0), errors="coerce").fillna(0.0)

    # harga (utama dari eco_place.csv: price_str = 'Rp…', price_num = parse)
    price_str_ser, price_num_ser = _resolve_price_columns(df)

    # lengkapi kolom opsional
    for col in ["place_name","place_description","category","city","address","image","gallery1","gallery2","gallery3","map_url"]:
        if col not in df.columns:
            df[col] = ""

    # insert
    rows = []
    for idx, r in df.iterrows():
        p = Place(
            id=int(r["id"]),
            place_name=str(r.get("place_name", "") or ""),
            place_description=str(r.get("place_description", "") or ""),
            category=str(r.get("category", "") or ""),
            city=str(r.get("city", "") or ""),
            address=str(r.get("address", "") or ""),
            price_num=float(price_num_ser.loc[idx] if idx in price_num_ser.index else 0.0),
            price_str=str(price_str_ser.loc[idx] if idx in price_str_ser.index else ""),
            rating_avg=float(r.get("rating_avg", 0.0) or 0.0),
            image=str(r.get("image", "") or ""),
            gallery1=str(r.get("gallery1", "") or ""),
            gallery2=str(r.get("gallery2", "") or ""),
            gallery3=str(r.get("gallery3", "") or ""),
            map_url=str(r.get("map_url", "") or ""),
        )
        rows.append(p)

    for p in rows:
        db_.session.add(p)
    db_.session.commit()

    non_empty_str = int((price_str_ser.fillna("").str.strip() != "").sum())
    non_zero_num = int((price_num_ser.fillna(0.0) > 0).sum())
    print(f"[seed] places terisi: {len(rows)} baris. price_str terisi: {non_empty_str}, price_num>0: {non_zero_num}")
