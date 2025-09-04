import React, { useEffect, useState } from "react";
import { api } from "../api";
import PlaceCard from "../components/PlaceCard";

export default function HomeAnonymous() {
  const [items, setItems] = useState([]);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    let mounted = true;
    (async () => {
      setBusy(true);
      try {
        const res = await api.get("/api/recs/anonymous?k=12");
        if (mounted) setItems(res.data || []);
      } catch (e) {
        console.error(e);
      } finally {
        if (mounted) setBusy(false);
      }
    })();
    return () => {
      mounted = false;
    };
  }, []);

  return (
    <div>
      <h1 className="text-xl font-semibold mb-4">
        Rekomendasi Populer (untuk pengunjung anonim)
      </h1>

      {busy && <div className="text-sm text-gray-500 mb-2">Memuat…</div>}

      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-4">
        {items.map((p) => (
          <PlaceCard key={p.place_id ?? p.id} p={p} />
        ))}
      </div>

      {!busy && items.length === 0 && (
        <div className="text-sm text-gray-500">Belum ada data rekomendasi.</div>
      )}
    </div>
  );
}
