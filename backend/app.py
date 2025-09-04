import os
from datetime import timedelta
from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_jwt_extended import (
    JWTManager, create_access_token, jwt_required, get_jwt_identity
)

from .models import db, User, Place, Rating, Comment, Bookmark
from .recommender import RecommenderService
from .utils import (
    hash_password, check_password, seed_places_if_empty,
    place_to_dict, display_price
)

def create_app():
    app = Flask(__name__)
    CORS(app, origins="*")

    # ===================== DB CONFIG =====================
    default_sqlite = "sqlite:///eco.db"
    app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", default_sqlite)
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    # JWT CONFIG
    app.config["JWT_SECRET_KEY"] = os.environ.get("JWT_SECRET_KEY", "dev-secret-key")
    app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(days=7)

    db.init_app(app)
    with app.app_context():
        db.create_all()
        seed_places_if_empty(db)
        # Debug tambahan biar tau koneksi DB kemana
        print("[DB CONNECTED]", db.engine.url)

    # Path model artefak
    base_dir = os.path.dirname(__file__)
    cbf_dir = os.path.join(base_dir, "models", "cbf")
    cf_dir  = os.path.join(base_dir, "models", "cf")
    data_dir = os.path.join(base_dir, "data")

    app.recs = RecommenderService(
        cbf_dir=os.environ.get("CBF_DIR", cbf_dir),
        cf_dir=os.environ.get("CF_DIR", cf_dir),
        fallback_data_dir=data_dir,
    )

    JWTManager(app)

    # ===================== AUTH =====================
    @app.post("/api/auth/register")
    def register():
        d = request.get_json(force=True) or {}
        name = (d.get("name") or "").strip()
        email = (d.get("email") or "").strip().lower()
        pw = d.get("password") or ""
        if not name or not email or not pw:
            return jsonify({"error": "Lengkapi name/email/password"}), 400
        if User.query.filter_by(email=email).first():
            return jsonify({"error": "Email sudah terdaftar"}), 400
        u = User(name=name, email=email, password_hash=hash_password(pw))
        db.session.add(u); db.session.commit()
        tok = create_access_token(identity=str(u.id))
        return jsonify({"token": tok, "user": {"id": u.id, "name": u.name, "email": u.email}})

    @app.post("/api/auth/login")
    def login():
        d = request.get_json(force=True) or {}
        email = (d.get("email") or "").strip().lower()
        pw = d.get("password") or ""
        u = User.query.filter_by(email=email).first()
        if not u or not check_password(pw, u.password_hash):
            return jsonify({"error": "Email atau password salah"}), 401
        tok = create_access_token(identity=str(u.id))
        return jsonify({"token": tok, "user": {"id": u.id, "name": u.name, "email": u.email}})

    @app.get("/api/auth/me")
    @jwt_required()
    def me():
        uid = int(get_jwt_identity())
        u = User.query.get_or_404(uid)
        return jsonify({"id": u.id, "name": u.name, "email": u.email})

    @app.post("/api/auth/logout")
    @jwt_required(optional=True)
    def logout():
        return jsonify({"ok": True})

    # ===================== PLACES =====================
    @app.get("/api/places")
    def list_places():
        q = request.args.get("q", "").strip().lower()
        city = request.args.get("city", "").strip().lower()
        cat = request.args.get("category", "").strip().lower()
        limit = int(request.args.get("limit", 20))

        query = Place.query
        if q:    query = query.filter(Place.place_name.ilike(f"%{q}%"))
        if city: query = query.filter(Place.city.ilike(f"%{city}%"))
        if cat:  query = query.filter(Place.category.ilike(f"%{cat}%"))

        rows = query.limit(limit).all()
        return jsonify([place_to_dict(p) for p in rows])

    @app.get("/api/places/<int:pid>")
    def place_detail(pid: int):
        p = Place.query.get_or_404(pid)
        return jsonify(place_to_dict(p, detail=True))

    @app.get("/api/places/sample")
    def sample_places():
        n = int(request.args.get("n", 18))
        df = app.recs.sample_places(n=n)
        ids = [int(x) for x in df["id"].tolist()]
        rows = Place.query.filter(Place.id.in_(ids)).all()
        price_map = {r.id: display_price(r.price_str, r.price_num) for r in rows}
        out = []
        for _, r in df.iterrows():
            pid = int(r["id"])
            out.append({
                "id": pid,
                "place_name": r.get("place_name", ""),
                "city": r.get("city", ""),
                "category": r.get("category", ""),
                "price": price_map.get(pid, "-"),
                "rating": float(r.get("rating", 0.0) or 0.0),
                "image": r.get("image", ""),
            })
        return jsonify(out)

    # ===================== RECOMMENDATIONS =====================
    @app.get("/api/recs/anonymous")
    def recs_anonymous():
        k = int(request.args.get("k", 20))
        df = app.recs.top_rated(k=k)
        ids = [int(x) for x in df["id"].tolist()]
        rows = Place.query.filter(Place.id.in_(ids)).all()
        price_map = {r.id: display_price(r.price_str, r.price_num) for r in rows}

        out = []
        for _, r in df.iterrows():
            pid = int(r["id"])
            out.append({
                "place_id": pid,
                "place_name": r.get("place_name", ""),
                "city": r.get("city", ""),
                "category": r.get("category", ""),
                "price": price_map.get(pid, "-"),
                "rating": float(r.get("rating", 0.0) or 0.0),
                "image": r.get("image", ""),
            })
        return jsonify(out)

    @app.get("/api/recs/hybrid")
    @jwt_required()
    def recs_hybrid():
        uid = int(get_jwt_identity())
        rows = Rating.query.filter_by(user_id=uid).all()
        user_ratings = {int(r.place_id): float(r.rating) for r in rows}
        if len(user_ratings) == 0:
            return jsonify({
                "need_onboarding": True,
                "message": "Belum ada preferensi. Klik beberapa kartu favorit untuk memulai."
            }), 428

        k = int(request.args.get("k", 20))
        alpha = float(os.environ.get("HYBRID_ALPHA", 0.6))
        df = app.recs.recommend_hybrid_for_user(user_ratings, k=k, alpha=alpha)

        ids = [int(x) for x in df.get("place_id", df.get("id"))]
        rows = Place.query.filter(Place.id.in_(ids)).all()
        price_map = {r.id: display_price(r.price_str, r.price_num) for r in rows}

        out = []
        for _, r in df.iterrows():
            pid = int(r.get("place_id", r.get("id")))
            out.append({
                "place_id": pid,
                "place_name": r.get("place_name", ""),
                "city": r.get("city", ""),
                "category": r.get("category", ""),
                "price": price_map.get(pid, "-"),
                "rating": float(r.get("rating", 0.0) or 0.0),
                "image": r.get("image", ""),
                "hybrid_score": float(r.get("hybrid_score", 0.0) or 0.0),
            })
        return jsonify(out)

    # ============================== ONBOARDING ==============================
    @app.post("/api/onboarding/like")
    @jwt_required()
    def onboarding_like():
        d = request.get_json(force=True) or {}
        ids = list(map(int, d.get("place_ids", [])))
        if not ids:
            return jsonify({"error": "place_ids kosong"}), 400
        uid = int(get_jwt_identity())
        for pid in ids:
            if not Place.query.get(pid):
                continue
            row = Rating.query.filter_by(user_id=uid, place_id=pid).first()
            if row: row.rating = 5.0
            else:   db.session.add(Rating(user_id=uid, place_id=pid, rating=5.0))
        db.session.commit()
        return jsonify({"ok": True, "count": len(ids)})

    # =============================== RATINGS ===============================
    @app.post("/api/ratings")
    @jwt_required()
    def add_rating():
        d = request.get_json(force=True) or {}
        uid = int(get_jwt_identity())
        pid = int(d.get("place_id"))
        val = float(d.get("rating", 0))
        if val < 1 or val > 5:
            return jsonify({"error": "Rating harus 1..5"}), 400
        row = Rating.query.filter_by(user_id=uid, place_id=pid).first()
        if row: row.rating = val
        else:   db.session.add(Rating(user_id=uid, place_id=pid, rating=val))
        db.session.commit()
        return jsonify({"ok": True})

    @app.get("/api/ratings/me")
    @jwt_required()
    def my_ratings():
        uid = int(get_jwt_identity())
        rows = Rating.query.filter_by(user_id=uid).all()
        return jsonify([{"place_id": r.place_id, "rating": r.rating} for r in rows])

    # ============================== COMMENTS ===============================
    @app.post("/api/comments")
    @jwt_required()
    def add_comment():
        d = request.get_json(force=True) or {}
        uid = int(get_jwt_identity())
        pid = int(d.get("place_id"))
        text = (d.get("text") or "").strip()
        if not text:
            return jsonify({"error": "Komentar kosong"}), 400
        c = Comment(user_id=uid, place_id=pid, text=text)
        db.session.add(c); db.session.commit()
        return jsonify({"ok": True, "comment_id": c.id})

    @app.get("/api/comments")
    def list_comments():
        pid = int(request.args.get("place_id"))
        rows = Comment.query.filter_by(place_id=pid).order_by(Comment.created_at.desc()).all()
        return jsonify([{
            "id": c.id, "user_id": c.user_id, "place_id": c.place_id,
            "text": c.text, "created_at": c.created_at.isoformat()
        } for c in rows])

    # ============================== BOOKMARKS ==============================
    @app.post("/api/bookmarks")
    @jwt_required()
    def add_bookmark():
        uid = int(get_jwt_identity())
        d = request.get_json(force=True) or {}
        pid = int(d.get("place_id"))
        if not Place.query.get(pid):
            return jsonify({"error": "Place tidak ditemukan"}), 404
        if Bookmark.query.filter_by(user_id=uid, place_id=pid).first():
            return jsonify({"ok": True, "already": True})
        db.session.add(Bookmark(user_id=uid, place_id=pid))
        db.session.commit()
        return jsonify({"ok": True})

    @app.delete("/api/bookmarks/<int:pid>")
    @jwt_required()
    def del_bookmark(pid: int):
        uid = int(get_jwt_identity())
        row = Bookmark.query.filter_by(user_id=uid, place_id=pid).first()
        if not row:
            return jsonify({"error": "Bookmark tidak ditemukan"}), 404
        db.session.delete(row); db.session.commit()
        return jsonify({"ok": True})

    @app.get("/api/bookmarks")
    @jwt_required()
    def list_bookmarks():
        uid = int(get_jwt_identity())
        rows = db.session.query(Bookmark, Place)\
            .join(Place, Bookmark.place_id == Place.id)\
            .filter(Bookmark.user_id == uid).all()
        out = []
        for b, p in rows:
            out.append({
                "place_id": p.id,
                "place_name": p.place_name,
                "city": p.city,
                "category": p.category,
                "price": display_price(p.price_str, p.price_num),  # string siap tampil
                "rating": p.rating_avg or 0.0,
                "image": p.image,
            })
        return jsonify(out)

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8000)), debug=True)
