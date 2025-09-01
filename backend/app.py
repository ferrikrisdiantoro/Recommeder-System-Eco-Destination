import os
import pandas as pd
from datetime import timedelta

from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_jwt_extended import (
    JWTManager, create_access_token, jwt_required, get_jwt_identity
)

from .models import db, User, Place, Rating, Comment, Bookmark
from .recommender import RecommenderService
from .utils import hash_password, check_password, parse_price_idr


def create_app():
    app = Flask(__name__)
    CORS(app, origins="*")  # Izinkan dipanggil dari domain frontend (Vite/localhost) tanpa error CORS.

    # ---- Config ----
    # DATABASE_URL: ganti kalau pakai Postgres/MySQL. Default SQLite file eco.db.
    app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get(
        "DATABASE_URL", "sqlite:///eco.db"
    )
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    # JWT_SECRET_KEY: ganti di production. Dipakai untuk menandatangani token login.
    app.config["JWT_SECRET_KEY"] = os.environ.get("JWT_SECRET_KEY", "dev-secret-key")
    # Token login berlaku 7 hari.
    app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(days=7)

    # ---- DB & seed ----
    db.init_app(app)
    with app.app_context():
        db.create_all()          # Buat tabel-tabel jika belum ada.
        seed_places_if_empty()   # Isi tabel places dari CSV sekali saja (kalau kosong).

    # ---- RECS: LOAD-ONLY dari folder models/cbf & models/cf ----
    # Folder artefak model (hasil dari notebook) bisa diubah via env CBF_DIR & CF_DIR.
    base_dir = os.path.dirname(__file__)
    data_dir = os.path.join(base_dir, "data")  # fallback baca eco_place.csv jika places_clean.csv tidak tersedia
    cbf_dir  = os.environ.get("CBF_DIR", os.path.join(base_dir, "models", "cbf"))
    cf_dir   = os.environ.get("CF_DIR",  os.path.join(base_dir, "models", "cf"))

    # Inisialisasi service rekomendasi. Di sini model tidak di-train ulang; hanya di-load.
    app.recs = RecommenderService(
        cbf_dir=cbf_dir,
        cf_dir=cf_dir,
        fallback_data_dir=data_dir,   # dipakai jika places_clean.csv tidak ada
    )

    # ---- JWT ----
    JWTManager(app)

    # =========================
    #           AUTH
    # =========================
    @app.post("/api/auth/register")
    def register():
        # Ambil input JSON dan validasi field wajib.
        d = request.get_json(force=True)
        name = (d.get("name") or "").strip()
        email = (d.get("email") or "").strip().lower()
        pw = d.get("password") or ""

        if not name or not email or not pw:
            return jsonify({"error": "Lengkapi name/email/password"}), 400
        if User.query.filter_by(email=email).first():
            return jsonify({"error": "Email sudah terdaftar"}), 400

        # Simpan user baru (password di-hash).
        u = User(name=name, email=email, password_hash=hash_password(pw))
        db.session.add(u)
        db.session.commit()

        # Buat token JWT untuk dipakai frontend.
        tok = create_access_token(identity=str(u.id))
        return jsonify({"token": tok, "user": {"id": u.id, "name": u.name, "email": u.email}})

    @app.post("/api/auth/login")
    def login():
        # Verifikasi kredensial: email & password.
        d = request.get_json(force=True)
        email = (d.get("email") or "").strip().lower()
        pw = d.get("password") or ""

        u = User.query.filter_by(email=email).first()
        if not u or not check_password(pw, u.password_hash):
            return jsonify({"error": "Email atau password salah"}), 401

        tok = create_access_token(identity=str(u.id))
        return jsonify({"token": tok, "user": {"id": u.id, "name": u.name, "email": u.email}})

    @app.get("/api/auth/me")
    @jwt_required()  # Endpoint hanya untuk user login; ambil identitas dari JWT.
    def me():
        uid = int(get_jwt_identity())
        u = User.query.get(uid)
        return jsonify({"id": u.id, "name": u.name, "email": u.email})

    @app.post("/api/auth/logout")
    @jwt_required(optional=True)  # Logout di sisi klien (hapus token). Di server cukup OK.
    def logout():
        return jsonify({"ok": True})

    # =========================
    #          PLACES
    # =========================
    @app.get("/api/places")
    def list_places():
        # Endpoint list tempat dengan filter sederhana (q/city/category).
        q = request.args.get("q", "").strip().lower()
        city = request.args.get("city", "").strip().lower()
        cat = request.args.get("category", "").strip().lower()
        limit = int(request.args.get("limit", 20))

        query = Place.query
        if q:
            query = query.filter(Place.place_name.ilike(f"%{q}%"))
        if city:
            query = query.filter(Place.city.ilike(f"%{city}%"))
        if cat:
            query = query.filter(Place.category.ilike(f"%{cat}%"))

        rows = query.limit(limit).all()
        return jsonify([place_to_dict(p) for p in rows])

    @app.get("/api/places/<int:pid>")
    def place_detail(pid: int):
        # Detail 1 tempat untuk halaman detail wisata.
        p = Place.query.get_or_404(pid)
        return jsonify(place_to_dict(p, detail=True))

    @app.get("/api/places/sample")
    def sample_places():
        # Ambil sampel random untuk onboarding (user baru memberi rating awal).
        n = int(request.args.get("n", 20))
        df = app.recs.sample_places(n=n)
        return jsonify(df.to_dict(orient="records"))

    # =========================
    #      RECOMMENDATIONS
    # =========================
    @app.get("/api/recs/anonymous")
    def recs_anonymous():
        # Rekomendasi untuk pengunjung anonim: top-rated secara global (tidak pakai preferensi user).
        k = int(request.args.get("k", 20))
        df = app.recs.top_rated(k=k)
        return jsonify(
            df[["id", "place_name", "city", "category", "price", "rating", "image"]]
            .rename(columns={"id": "place_id"})
            .to_dict(orient="records")
        )

    @app.get("/api/recs/hybrid")
    @jwt_required()
    def recs_hybrid():
        # Rekomendasi HYBRID (CF+CBF) untuk user login.
        uid = int(get_jwt_identity())

        # Ambil semua rating user dari DB → jadi dict {place_id: rating}
        rows = Rating.query.filter_by(user_id=uid).all()
        user_ratings = {int(r.place_id): float(r.rating) for r in rows}

        # Jika belum ada rating, kembalikan 428 untuk memicu onboarding di FE.
        if len(user_ratings) == 0:
            return (
                jsonify(
                    {
                        "need_onboarding": True,
                        "message": "Belum ada rating. Silakan beri rating awal agar rekomendasi lebih akurat.",
                    }
                ),
                428,
            )

        # Alpha = bobot CF vs CBF. Bisa disetel via env HYBRID_ALPHA.
        k = int(request.args.get("k", 20))
        alpha = float(os.environ.get("HYBRID_ALPHA", 0.6))

        # Hitung rekomendasi ke service (blend CF+CBF, masking item yang sudah dirating).
        df = app.recs.recommend_hybrid_for_user(user_ratings, k=k, alpha=alpha)
        return jsonify(df.to_dict(orient="records"))

    # =========================
    #    RATINGS & COMMENTS
    # =========================
    @app.post("/api/ratings")
    @jwt_required()
    def add_rating():
        # Simpan/Update rating user untuk 1 tempat (1..5).
        d = request.get_json(force=True)
        uid = int(get_jwt_identity())
        pid = int(d.get("place_id"))
        val = float(d.get("rating", 0))

        if val < 1 or val > 5:
            return jsonify({"error": "Rating harus 1..5"}), 400

        row = Rating.query.filter_by(user_id=uid, place_id=pid).first()
        if row:
            row.rating = val  # update
        else:
            db.session.add(Rating(user_id=uid, place_id=pid, rating=val))  # insert
        db.session.commit()
        return jsonify({"ok": True})

    @app.get("/api/ratings/me")
    @jwt_required()
    def my_ratings():
        # Ambil semua rating milik user login (untuk ditampilkan di UI bila perlu).
        uid = int(get_jwt_identity())
        rows = Rating.query.filter_by(user_id=uid).all()
        return jsonify([{"place_id": r.place_id, "rating": r.rating} for r in rows])

    @app.post("/api/comments")
    @jwt_required()
    def add_comment():
        # Tambahkan komentar pada sebuah tempat (disimpan di DB).
        d = request.get_json(force=True)
        uid = int(get_jwt_identity())
        pid = int(d.get("place_id"))
        text = (d.get("text") or "").strip()

        if not text:
            return jsonify({"error": "Komentar kosong"}), 400

        c = Comment(user_id=uid, place_id=pid, text=text)
        db.session.add(c)
        db.session.commit()
        return jsonify({"ok": True, "comment_id": c.id})

    @app.get("/api/comments")
    def list_comments():
        # Ambil list komentar untuk 1 tempat (urut terbaru).
        pid = int(request.args.get("place_id"))
        rows = (
            Comment.query.filter_by(place_id=pid)
            .order_by(Comment.created_at.desc())
            .all()
        )
        return jsonify(
            [
                {
                    "id": c.id,
                    "user_id": c.user_id,
                    "place_id": c.place_id,
                    "text": c.text,
                    "created_at": c.created_at.isoformat(),
                }
                for c in rows
            ]
        )

    # =========================
    #         BOOKMARKS
    # =========================
    @app.post("/api/bookmarks")
    @jwt_required()
    def add_bookmark():
        # Simpan bookmark tempat untuk user login.
        uid = int(get_jwt_identity())
        d = request.get_json(force=True)
        pid = int(d.get("place_id"))

        if not Place.query.get(pid):
            return jsonify({"error": "Place tidak ditemukan"}), 404
        if Bookmark.query.filter_by(user_id=uid, place_id=pid).first():
            return jsonify({"ok": True, "already": True})  # idempotent

        db.session.add(Bookmark(user_id=uid, place_id=pid))
        db.session.commit()
        return jsonify({"ok": True})

    @app.delete("/api/bookmarks/<int:pid>")
    @jwt_required()
    def del_bookmark(pid: int):
        # Hapus bookmark satu tempat untuk user login.
        uid = int(get_jwt_identity())
        row = Bookmark.query.filter_by(user_id=uid, place_id=pid).first()
        if not row:
            return jsonify({"error": "Bookmark tidak ditemukan"}), 404
        db.session.delete(row)
        db.session.commit()
        return jsonify({"ok": True})

    @app.get("/api/bookmarks")
    @jwt_required()
    def list_bookmarks():
        # Ambil daftar bookmark + metadata tempat (join).
        uid = int(get_jwt_identity())
        rows = (
            db.session.query(Bookmark, Place)
            .join(Place, Bookmark.place_id == Place.id)
            .filter(Bookmark.user_id == uid)
            .all()
        )
        out = []
        for b, p in rows:
            out.append(
                {
                    "place_id": p.id,
                    "place_name": p.place_name,
                    "city": p.city,
                    "category": p.category,
                    "price": p.price_str or "",
                    "rating": p.rating_avg or 0.0,
                    "image": p.image,
                }
            )
        return jsonify(out)

    return app


def place_to_dict(p: Place, detail: bool = False):
    """
    Serializer: ubah object Place → dict JSON untuk frontend.
    detail=True menambahkan kolom tambahan untuk halaman detail.
    """
    d = {
        "place_id": p.id,
        "place_name": p.place_name,
        "city": p.city,
        "category": p.category,
        "price": p.price_str or "",
        "rating": p.rating_avg or 0.0,
        "image": p.image,
    }
    if detail:
        d.update(
            {
                "description": p.place_description,
                "address": p.address,
                "gallery1": p.gallery1,
                "gallery2": p.gallery2,
                "gallery3": p.gallery3,
                "map_url": p.map_url,
            }
        )
    return d


def seed_places_if_empty():
    """Seed tabel places dari data/eco_place.csv (sekali saja saat tabel masih kosong)."""
    if Place.query.first():
        return  # sudah ada data → tidak perlu seed

    csv_path = os.path.join(os.path.dirname(__file__), "data", "eco_place.csv")
    if not os.path.exists(csv_path):
        return

    df = pd.read_csv(csv_path)

    # Peta nama kolom CSV → kolom tabel
    colmap = {
        "place_id": "id",
        "place_name": "place_name",
        "place_description": "place_description",
        "category": "category",
        "city": "city",
        "description_location": "address",
        "place_img": "image",
        "gallery_photo_img1": "gallery1",
        "gallery_photo_img2": "gallery2",
        "gallery_photo_img3": "gallery3",
        "place_map": "map_url",
        "price": "price",
        "rating": "rating",
    }

    # Pastikan semua kolom ada (kalau tidak ada, buat kosong).
    for c in colmap.keys():
        if c not in df.columns:
            df[c] = ""

    df = df[list(colmap.keys())].rename(columns=colmap)

    # price_num (float) diisi dari price string (Rp…).
    df["price_num"] = df["price"].apply(parse_price_idr)
    # rating jadi float (NaN→0).
    df["rating"] = pd.to_numeric(df["rating"], errors="coerce").fillna(0.0)

    # Insert baris-baris Place ke DB.
    rows = []
    for _, r in df.iterrows():
        p = Place(
            id=int(r["id"]),
            place_name=r["place_name"] or "",
            place_description=r["place_description"] or "",
            category=r["category"] or "",
            city=r["city"] or "",
            address=r["address"] or "",
            price_num=float(r["price_num"] or 0.0),
            price_str=r["price"] or "",
            rating_avg=float(r["rating"] or 0.0),
            image=r["image"] or "",
            gallery1=r["gallery1"] or "",
            gallery2=r["gallery2"] or "",
            gallery3=r["gallery3"] or "",
            map_url=r["map_url"] or "",
        )
        rows.append(p)

    for p in rows:
        db.session.add(p)
    db.session.commit()


if __name__ == "__main__":
    # Mode jalankan langsung (tanpa flask run). Port default 8000.
    app = create_app()
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8000)), debug=True)
