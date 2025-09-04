import React, { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { api } from "../api";
import RatingStars from "../components/RatingStars";
import { asPriceText, formatRating } from "../utils/format";

export default function Detail() {
  const { id } = useParams();
  const [p, setP] = useState(null);
  const [comments, setComments] = useState([]);
  const [myRating, setMyRating] = useState(0);
  const [text, setText] = useState("");
  const [busy, setBusy] = useState(false);

  const load = async () => {
    setBusy(true);
    try {
      const [pr, cr] = await Promise.all([
        api.get(`/api/places/${id}`),
        api.get(`/api/comments?place_id=${id}`),
      ]);
      setP(pr.data);
      setComments(cr.data || []);
    } catch (e) {
      console.error(e);
    } finally {
      setBusy(false);
    }
  };

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id]);

  const bookmark = async () => {
    try {
      await api.post("/api/bookmarks", { place_id: Number(id) });
      alert("Ditambahkan ke bookmark");
    } catch (e) {
      alert("Login dulu untuk bookmark.");
    }
  };

  const saveRating = async () => {
    if (!myRating) {
      alert("Pilih rating 1..5");
      return;
    }
    try {
      await api.post("/api/ratings", { place_id: Number(id), rating: myRating });
      alert("Rating disimpan");
    } catch (e) {
      alert("Login dulu untuk beri rating.");
    }
  };

  const sendComment = async () => {
    const t = text.trim();
    if (!t) return;
    try {
      await api.post("/api/comments", { place_id: Number(id), text: t });
      setText("");
      await load();
    } catch (e) {
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

      <div className="mt-6">
        <h2 className="font-semibold mb-2">Galeri</h2>
        <div className="grid grid-cols-3 gap-3">
          {[p.gallery1, p.gallery2, p.gallery3]
            .filter(Boolean)
            .map((g, idx) => (
              <img
                key={idx}
                src={g}
                alt={`Galeri ${idx + 1}`}
                className="w-full h-40 object-cover rounded-lg"
                loading="lazy"
              />
            ))}
        </div>
      </div>

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

      <div className="mt-6">
        <h2 className="font-semibold mb-2">Komentar</h2>

        <div className="flex gap-2">
          <input
            className="flex-1 border p-2 rounded"
            placeholder="Tulis komentar..."
            value={text}
            onChange={(e) => setText(e.target.value)}
          />
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
