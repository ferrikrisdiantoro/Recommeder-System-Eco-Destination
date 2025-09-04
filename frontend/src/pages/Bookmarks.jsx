import React, { useEffect, useState } from "react";
import { api } from "../api";
import PlaceCard from "../components/PlaceCard";

export default function Bookmarks() {
  const [items, setItems] = useState([]);
  const [busy, setBusy] = useState(false);

  const load = async () => {
    setBusy(true);
    try {
      const res = await api.get("/api/bookmarks");
      setItems(res.data || []);
    } catch (e) {
      console.error(e);
    } finally {
      setBusy(false);
    }
  };

  useEffect(() => {
    load();
  }, []);

  const del = async (p) => {
    if (!confirm("Hapus bookmark?")) return;
    try {
      await api.delete(`/api/bookmarks/${p.place_id ?? p.id}`);
      await load();
    } catch (e) {
      alert("Gagal hapus bookmark");
    }
  };

  return (
    <div>
      <h1 className="text-xl font-semibold mb-4">Bookmarks</h1>

      {busy && <div className="text-sm text-gray-500 mb-2">Memuat…</div>}

      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-4">
        {items.map((p) => (
          <div key={p.place_id ?? p.id} className="relative">
            <PlaceCard p={p} />
            <button
              type="button"
              onClick={() => del(p)}
              className="absolute top-2 right-2 px-2 py-1 text-xs rounded bg-red-600 text-white"
            >
              Delete
            </button>
          </div>
        ))}
      </div>

      {!busy && items.length === 0 && (
        <div className="text-sm text-gray-500">Belum ada bookmark.</div>
      )}
    </div>
  );
}
