import os
import numpy as np
import pandas as pd
import joblib
from pathlib import Path

from scipy.sparse import load_npz
from sklearn.metrics.pairwise import cosine_similarity

import warnings
try:
    # suppress warning beda versi saat unpickle (artefak dibuat dgn versi sklearn berbeda)
    from sklearn.exceptions import InconsistentVersionWarning
except Exception:
    class InconsistentVersionWarning(Warning):
        pass


class RecommenderService:
    """
    Service rekomendasi yang HANYA LOAD artefak (tidak training).
    Struktur artefak:
      - CBF (di cbf_dir):
          * cbf_item_matrix.npz       → matriks fitur item (teks TF-IDF + numerik scaled)
          * cbf_artifacts.joblib      → { tfidf, scaler, num_cols, place_id_order }
          * places_clean.csv (opsi)   → metadata tempat yang sudah diselaraskan
      - CF (di cf_dir):
          * cf_item_sim.npy           → matriks similarity item-item (berbasis rating)
          * cf_artifacts.joblib       → { item_ids, item_to_col }
    """

    def __init__(self, cbf_dir: str, cf_dir: str, fallback_data_dir: str | None = None):
        self.cbf_dir = Path(cbf_dir)
        self.cf_dir = Path(cf_dir)
        self.fallback_data_dir = Path(fallback_data_dir) if fallback_data_dir else None

        # Data & artefak yang diload
        self.places_df: pd.DataFrame | None = None   # metadata item untuk kirim ke UI
        self.place_id_order: list[int] = []          # urutan baris CBF (mapping id → row)
        self.X = None                                # matriks CBF (sparse)
        self.tfidf = None
        self.scaler = None
        self.num_cols: list[str] = []

        self.item_sim = None       # matriks similarity CF (ndarray)
        self.item_ids: list[int] = []                # urutan kolom CF
        self.item_to_col: dict[int, int] = {}        # mapping place_id → index kolom CF

        self._load_all()  # langsung load semua saat service dibuat

    # ---------- Public APIs ----------
    def top_rated(self, k=20):
        """Untuk pengunjung anonim: ambil tempat dengan rating tertinggi."""
        df = self.places_df.copy()
        return df.sort_values("rating", ascending=False).head(k)

    def sample_places(self, n=20, seed=42):
        """Ambil sampel random tempat untuk halaman onboarding (beri rating awal)."""
        df = self.places_df.sample(n=min(n, len(self.places_df)), random_state=seed)
        return df[["id", "place_name", "city", "category", "price", "rating", "image"]]

    def recommend_hybrid_for_user(self, user_ratings: dict, k=20, alpha=0.6):
        """
        Rekomendasi HYBRID (CF + CBF):
          - s_cf: skor dari pola rating antar item (item-item similarity)
          - s_cbf: skor dari kemiripan konten (TF-IDF + numerik)
          - Normalisasi 0..1 lalu blend: s = alpha*s_cf + (1-alpha)*s_cbf
          - Item yang sudah dirating user dimask agar tidak direkomendasikan ulang.
        """
        # --- CF score ---
        # Bentuk vektor rating sementara sepanjang jumlah item CF.
        s_cf = np.zeros(len(self.item_ids), dtype=float)
        if self.item_sim is not None and len(self.item_ids) > 0:
            v = np.zeros(len(self.item_ids), dtype=float)  # semua 0 (belum rating)
            for pid, r in (user_ratings or {}).items():
                j = self.item_to_col.get(int(pid))  # cari kolom item CF
                if j is not None:
                    v[j] = float(r)                 # isi rating user untuk item tersebut
            s_cf = self.item_sim.dot(v)             # skor = kombinasi kemiripan * rating

        # --- CBF score (linear comb of similarities) ---
        # s_cbf dihitung di ruang konten (CBF), berdasarkan cosine dari vektor fitur item.
        s_cbf = np.zeros(len(self.place_id_order), dtype=float)
        if self.X is not None:
            pid_to_row = {pid: i for i, pid in enumerate(self.place_id_order)}
            for pid, r in (user_ratings or {}).items():
                i = pid_to_row.get(int(pid))        # baris CBF untuk item yang dirating user
                if i is not None:
                    sims = cosine_similarity(self.X[i], self.X).ravel()  # kemiripan ke semua item
                    s_cbf += sims * float(r)        # boboti sesuai rating user

        # --- Mask already-seen (from CF space) ---
        # Agar tidak menyarankan item yang sudah dirating user.
        seen_cols = set()
        for pid in (user_ratings or {}):
            j = self.item_to_col.get(int(pid))
            if j is not None:
                seen_cols.add(j)

        # --- Align CBF score to CF order ---
        # s_cbf masih dalam urutan CBF; perlu disejajarkan dengan urutan item CF.
        pid_to_row = {pid: i for i, pid in enumerate(self.place_id_order)}
        s_cbf_aligned = np.zeros_like(s_cf)
        for idx, pid in enumerate(self.item_ids):
            i = pid_to_row.get(pid)
            if i is not None:
                s_cbf_aligned[idx] = s_cbf[i]

        # --- Normalize helper ---
        # Bawa ke 0..1 agar skala CF & CBF adil saat digabung.
        def norm01(x: np.ndarray) -> np.ndarray:
            mn, mx = np.nanmin(x), np.nanmax(x)
            if not np.isfinite(mn) or not np.isfinite(mx) or mx - mn < 1e-9:
                return np.zeros_like(x)
            return (x - mn) / (mx - mn + 1e-9)

        # Blend dengan alpha: makin besar alpha -> CF lebih dominan.
        s = alpha * norm01(s_cf) + (1 - alpha) * norm01(s_cbf_aligned)

        # Mask tempat yang sudah dirating (set -inf).
        for j in seen_cols:
            s[j] = -np.inf

        # Ambil Top-K skor terbesar.
        k = min(k, len(s) - 1) if len(s) > 1 else 1
        top_idx = np.argpartition(-s, kth=k - 1)[:k]
        top_idx = top_idx[np.argsort(-s[top_idx])]

        # Petakan index CF → place_id → lengkapi metadata untuk UI.
        top_pids = [self.item_ids[j] for j in top_idx]
        cols = ["place_name", "city", "category", "price", "rating", "image"]
        meta = (
            self.places_df.set_index("id")
            .reindex(top_pids)[cols]
            .reset_index()
            .rename(columns={"index": "place_id"})
        )
        meta["hybrid_score"] = np.array(s[top_idx]).round(4)  # untuk debugging/penjelasan di UI
        return meta

    # ---------- Loaders ----------
    def _load_all(self):
        """Load artefak CBF & CF, lalu ratakan ID supaya konsisten."""
        self._load_cbf()
        self._load_cf()
        self._sanity_align_ids()

    def _load_cbf(self):
        """Load artefak Content-Based Filtering + metadata places."""
        mat_p = self.cbf_dir / "cbf_item_matrix.npz"
        art_p = self.cbf_dir / "cbf_artifacts.joblib"

        if not (mat_p.exists() and art_p.exists()):
            raise FileNotFoundError(
                f"CBF artefak tidak ditemukan di {self.cbf_dir}. "
                f"Harus ada 'cbf_item_matrix.npz' dan 'cbf_artifacts.joblib'."
            )

        # Load artifacts (suppress warning beda versi sklearn).
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", InconsistentVersionWarning)
            obj = joblib.load(art_p)

        self.tfidf = obj.get("tfidf")
        self.scaler = obj.get("scaler")
        self.num_cols = obj.get("num_cols", [])
        self.place_id_order = list(obj.get("place_id_order", []))
        self.X = load_npz(mat_p)  # matriks fitur item (sparse)

        # ---- Load places metadata ----
        df = None
        places_csv = self.cbf_dir / "places_clean.csv"
        if places_csv.exists():
            # Lebih konsisten karena dibuat bersama artefak.
            df = pd.read_csv(places_csv)
        else:
            # Fallback ke data mentah eco_place.csv.
            if not self.fallback_data_dir:
                raise FileNotFoundError(
                    "places_clean.csv tidak ada dan fallback_data_dir tidak diset."
                )
            eco_p = self.fallback_data_dir / "eco_place.csv"
            if not eco_p.exists():
                raise FileNotFoundError(
                    f"places_clean.csv tidak ada dan {eco_p} juga tidak ditemukan."
                )
            raw = pd.read_csv(eco_p)
            # Samakan nama kolom agar konsisten.
            raw = raw.rename(
                columns={
                    "place_id": "id",
                    "place_img": "image",
                    "description_location": "address",
                    "gallery_photo_img1": "gallery1",
                    "gallery_photo_img2": "gallery2",
                    "gallery_photo_img3": "gallery3",
                    "place_map": "map_url",
                }
            )
            keep = [
                "id", "place_name", "place_description", "category", "city",
                "address", "price", "rating", "image", "gallery1", "gallery2", "gallery3", "map_url"
            ]
            for c in keep:
                if c not in raw.columns:
                    raw[c] = "" if c not in ["rating"] else 0.0
            df = raw[keep].copy()

        # ---- Normalisasi kolom ----
        cols_have = set(df.columns)

        # Pastikan ada kolom id (kalau belum, coba rename/tebak dari place_id/Unnamed:0)
        if "id" not in cols_have:
            if "place_id" in cols_have:
                df = df.rename(columns={"place_id": "id"})
            elif "Unnamed: 0" in cols_have:
                df = df.rename(columns={"Unnamed: 0": "id"})
            elif self.place_id_order and len(self.place_id_order) == len(df):
                df = df.copy()
                df["id"] = list(self.place_id_order)
            else:
                raise KeyError(
                    f"Tidak menemukan kolom 'id' pada places, kolom tersedia: {sorted(cols_have)}.\n"
                    f"Tambahkan kolom 'id' atau 'place_id', atau sertakan places_clean.csv yang konsisten."
                )

        # Pastikan kolom yang dipakai UI ada (price/image), rename bila perlu.
        if "price" not in df.columns and "price_str" in df.columns:
            df = df.rename(columns={"price_str": "price"})
        if "image" not in df.columns and "place_img" in df.columns:
            df = df.rename(columns={"place_img": "image"})
        for col in ["place_name", "category", "city", "price", "image"]:
            if col not in df.columns:
                df[col] = ""

        # Tipe aman: id → int, rating → float (NaN jadi 0.0)
        df["id"] = pd.to_numeric(df["id"], errors="coerce").astype("Int64")
        df = df.dropna(subset=["id"]).astype({"id": int})
        df["rating"] = pd.to_numeric(df.get("rating", 0.0), errors="coerce").fillna(0.0)

        self.places_df = df

    def _load_cf(self):
        """Load artefak Collaborative Filtering (item-item similarity)."""
        sim_p = self.cf_dir / "cf_item_sim.npy"
        art_p = self.cf_dir / "cf_artifacts.joblib"

        if not (sim_p.exists() and art_p.exists()):
            raise FileNotFoundError(
                f"CF artefak tidak ditemukan di {self.cf_dir}. "
                f"Harus ada 'cf_item_sim.npy' dan 'cf_artifacts.joblib'."
            )

        self.item_sim = np.load(sim_p)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", InconsistentVersionWarning)
            obj = joblib.load(art_p)
        self.item_ids = list(obj.get("item_ids", []))
        self.item_to_col = dict(obj.get("item_to_col", {}))

    def _sanity_align_ids(self):
        """
        Ratakan konsistensi ID:
        - Kalau ada id di CF yang tidak ada di metadata places → drop baris/kolom similarity tsb.
        - Susun ulang mapping item_to_col agar sesuai index baru.
        """
        valid_ids = set(self.places_df["id"].tolist())
        if not self.item_ids:
            return

        keep_mask = np.array([pid in valid_ids for pid in self.item_ids], dtype=bool)
        if keep_mask.size and (not keep_mask.all()):
            idx = np.where(keep_mask)[0]
            # Potong matriks similarity ke item yang valid saja.
            self.item_sim = self.item_sim[np.ix_(idx, idx)]
            # Susun ulang daftar item dan mapping-nya.
            self.item_ids = [self.item_ids[i] for i in idx]
            self.item_to_col = {pid: j for j, pid in enumerate(self.item_ids)}
