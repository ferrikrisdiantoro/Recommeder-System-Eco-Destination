import React, { useEffect, useState, useCallback } from "react";
import { useParams } from "react-router-dom";
import { api } from "../api";
import RatingStars from "../components/RatingStars";
import { asPriceText, formatRating } from "../utils/format";

export default function Detail() {
  const { id } = useParams();
  const [p, setP] = useState(null);
  const [comments, setComments] = useState([]);
  const [ratingsPub, setRatingsPub] = useState({ avg: 0, count: 0, items: [] });
  const [myRating, setMyRating] = useState(0);
  const [text, setText] = useState("");
  const [busy, setBusy] = useState(false);

  const loadPlace = useCallback(async () => {
    const res = await api.get(`/api/places/${id}`);
    const data = res.data || {};
    setP(data);
    // ambil my_rating dari server agar persist setelah refresh
    setMyRating(Number(data.my_rating || 0));
  }, [id]);

  const loadComments = useCallback(async () => {
    const cr = await api.get(`/api/comments?place_id=${id}`);
    setComments(cr.data || []);
  }, [id]);

  const loadRatingsPub = useCallback(async () => {
    const rr = await api.get(`/api/ratings/for_place?place_id=${id}`);
    setRatingsPub(rr.data || { avg: 0, count: 0, items: [] });
  }, [id]);

  const loadAll = useCallback(async () => {
    setBusy(true);
    try {
      await Promise.all([loadPlace(), loadComments(), loadRatingsPub()]);
    } finally {
      setBusy(false);
    }
  }, [loadPlace, loadComments, loadRatingsPub]);

  useEffect(() => {
    loadAll();
  }, [loadAll]);

  const bookmark = async () => {
    try {
      await api.post("/api/bookmarks", { place_id: Number(id) });
      alert("Ditambahkan ke bookmark");
    } catch {
      alert("Login dulu untuk bookmark.");
    }
  };

  const saveRating = async () => {
    if (!myRating) {
      alert("Pilih rating 1..5");
      return;
    }
    try {
      const r = await api.post("/api/ratings", { place_id: Number(id), rating: myRating });
      const { avg, count } = r.data || {};
      // update angka agregat di UI tanpa reload penuh
      setP((prev) => prev ? { ...prev, rating: avg, rating_count: count } : prev);
      await loadRatingsPub(); // refresh daftar rating publik
      alert("Rating disimpan");

      // Sinyal ke halaman HomeAuth agar refetch (dua jalur: event & localStorage)
      window.dispatchEvent(new Event("recs:bump"));
      localStorage.setItem("recs.bump", String(Date.now()));
    } catch {
      alert("Login dulu untuk beri rating.");
    }
  };

  const sendComment = async () => {
    const t = text.trim();
    if (!t) return;
    try {
      await api.post("/api/comments", { place_id: Number(id), text: t });
      setText("");
      await loadComments();
    } catch {
      alert("Login dulu untuk komentar.");
    }
  };

  if (busy && !p) return <div>Loading…</div>;
  if (!p) return <div>Data tidak ditemukan.</div>;

  const priceText = p.price_text ?? asPriceText(p.price);

  return (
    <div className="max-w-4xl mx-auto">
      <div className="grid md:grid-cols-2 gap-4">
        <img
          src={p.image}
          alt={p.place_name || "Tempat"}
          className="w-full h-72 object-cover rounded-xl"
        />

        <div>
          <h1 className="text-2xl font-semibold">{p.place_name}</h1>
          <div className="text-gray-600">
            {p.city || "-"} • {p.category || "-"}
          </div>

          <div className="mt-2">
            Harga: <b>{priceText}</b>
          </div>
          <div className="mt-1">
            Rating: <b>{formatRating(p.rating)}</b>
            {typeof p.rating_count === "number" && (
              <span className="text-gray-500"> ({p.rating_count})</span>
            )}
          </div>

          {p.description && (
            <div className="mt-2 text-gray-700">{p.description}</div>
          )}
          {p.address && (
            <div className="mt-2 text-gray-700">Alamat: {p.address}</div>
          )}

          <div className="mt-3 flex gap-2">
            <button
              type="button"
              onClick={bookmark}
              className="px-3 py-2 rounded bg-black text-white"
            >
              Bookmark
            </button>

            {p.map_url && (
              <a
                href={p.map_url}
                target="_blank"
                rel="noopener noreferrer"
                className="px-3 py-2 rounded border"
              >
                Map
              </a>
            )}
          </div>
        </div>
      </div>

      {/* My rating */}
      <div className="mt-6">
        <h2 className="font-semibold mb-2">Beri Rating</h2>
        <RatingStars value={myRating} onChange={setMyRating} />
        <button
          type="button"
          onClick={saveRating}
          className="mt-2 px-3 py-1 rounded bg-black text-white"
        >
          Simpan
        </button>
      </div>

      {/* Rating publik seperti Google */}
      <div className="mt-6">
        <h2 className="font-semibold mb-2">Rating Pengunjung</h2>
        <div className="text-sm text-gray-600 mb-2">
          Rata-rata: <b>{formatRating(ratingsPub.avg)}</b>{" "}
          {ratingsPub.count ? <>({ratingsPub.count} rating)</> : null}
        </div>
        <div className="space-y-2">
          {ratingsPub.items.map((it) => (
            <div key={it.id} className="bg-white p-3 rounded border">
              <div className="text-sm text-gray-500">
                {it.user_name} • {new Date(it.created_at).toLocaleString()}
              </div>
              <div className="font-medium">Rating: {formatRating(it.rating)}</div>
            </div>
          ))}
          {ratingsPub.items.length === 0 && (
            <div className="text-sm text-gray-500">Belum ada rating publik.</div>
          )}
        </div>
      </div>

      {/* Komentar publik */}
      <div className="mt-6">
        <h2 className="font-semibold mb-2">Komentar</h2>

        <div className="flex gap-2">
          <input
            className="flex-1 border p-2 rounded"
            placeholder="Tulis komentar..."
            value={text}
            onChange={(e) => setText(e.target.value)}
          />
        </div>
        <div className="mt-2">
          <button
            type="button"
            onClick={sendComment}
            className="px-3 py-1 rounded bg-black text-white"
          >
            Kirim
          </button>
        </div>

        <div className="mt-3 space-y-2">
          {comments.map((c) => (
            <div key={c.id} className="bg-white p-3 rounded border">
              <div className="text-sm text-gray-500">
                {c.user_name ? `${c.user_name} • ` : ""}
                {c.created_at ? new Date(c.created_at).toLocaleString() : ""}
              </div>
              <div>{c.text}</div>
            </div>
          ))}
          {comments.length === 0 && (
            <div className="text-sm text-gray-500">Belum ada komentar.</div>
          )}
        </div>
      </div>
    </div>
  );
}
