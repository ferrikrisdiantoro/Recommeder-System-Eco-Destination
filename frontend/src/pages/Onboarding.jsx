import React, { useEffect, useState } from "react";
import { api } from "../api";
import SelectableCard from "../components/SelectableCard";

export default function Onboarding() {
  const [items, setItems] = useState([]);
  const [selected, setSelected] = useState(new Set());
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    (async () => {
      try {
        const res = await api.get("/api/places/sample?n=18");
        setItems(res.data || []);
      } catch (e) {
        console.error(e);
      }
    })();
  }, []);

  const toggle = (it) => {
    const pid = it.id || it.place_id;
    setSelected((prev) => {
      const next = new Set(prev);
      if (next.has(pid)) next.delete(pid);
      else next.add(pid);
      return next;
    });
  };

  const submit = async () => {
    if (selected.size === 0) {
      alert("Pilih minimal 1 tempat yang kamu suka.");
      return;
    }
    setBusy(true);
    try {
      await api.post("/api/onboarding/like", {
        place_ids: Array.from(selected),
      });
      alert("Terima kasih! Rekomendasi siap.");
      window.location.href = "/home";
    } catch (e) {
      alert("Gagal menyimpan preferensi (pastikan login).");
    } finally {
      setBusy(false);
    }
  };

  return (
    <div>
      <h1 className="text-xl font-semibold mb-2">Pilih Beberapa Tempat Favorit</h1>
      <p className="text-gray-600 mb-4">
        Cukup klik kartu yang kamu suka. Sistem akan menandai sebagai rating 5.
      </p>

      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-4">
        {items.map((it) => {
          const pid = it.id || it.place_id;
          return (
            <SelectableCard
              key={pid}
              item={it}
              selected={selected.has(pid)}
              onToggle={toggle}
            />
          );
        })}
      </div>

      <div className="mt-5">
        <button
          type="button"
          onClick={submit}
          disabled={busy}
          className="px-4 py-2 rounded bg-black text-white disabled:opacity-60"
        >
          {busy ? "Menyimpan..." : "Simpan & Lihat Rekomendasi"}
        </button>
      </div>
    </div>
  );
}
