import React, { useEffect, useState, useCallback, useRef } from "react";
import { api } from "../api";
import PlaceCard from "../components/PlaceCard";

export default function HomeAuth() {
  const [items, setItems] = useState([]);
  const [need, setNeed] = useState(false);
  const [msg, setMsg] = useState("");
  const [busy, setBusy] = useState(false);
  const [version, setVersion] = useState(0); // pemicu refetch
  const lastBumpRef = useRef(localStorage.getItem("recs.bump") || "");

  const load = useCallback(async () => {
    setBusy(true);
    try {
      const res = await api.get("/api/recs/hybrid?k=12");
      setItems(res.data || []);
      setNeed(false);
      setMsg("");
    } catch (err) {
      if (err?.response?.status === 428) {
        setNeed(true);
        setMsg(err?.response?.data?.message || "Silakan onboarding dulu.");
        setItems([]);
      } else {
        console.error(err);
      }
    } finally {
      setBusy(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load, version]);

  // Dengarkan event global dari halaman Detail (dipicu setelah simpan rating)
  useEffect(() => {
    const onBump = () => setVersion((v) => v + 1);
    window.addEventListener("recs:bump", onBump);
    return () => window.removeEventListener("recs:bump", onBump);
  }, []);

  // Tambahan: dengarkan perubahan localStorage (robust saat navigasi/tab lain)
  useEffect(() => {
    const onStorage = (e) => {
      if (e.key === "recs.bump") setVersion((v) => v + 1);
    };
    window.addEventListener("storage", onStorage);

    // saat pertama mount, cek apakah ada bump yang terjadi sebelum halaman ini dibuka
    const now = localStorage.getItem("recs.bump") || "";
    if (now && now !== lastBumpRef.current) {
      lastBumpRef.current = now;
      setVersion((v) => v + 1);
    }

    return () => window.removeEventListener("storage", onStorage);
  }, []);

  if (need) {
    return (
      <div>
        <h1 className="text-xl font-semibold mb-2">Butuh Onboarding</h1>
        <p className="mb-4">{msg}</p>
        <a className="px-3 py-2 rounded bg-black text-white" href="/onboarding">
          Mulai Onboarding
        </a>
      </div>
    );
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-4">
        <h1 className="text-xl font-semibold">Rekomendasi AI (Hybrid)</h1>
        <button
          type="button"
          onClick={() => setVersion((v) => v + 1)}
          className="px-3 py-1 rounded border text-sm"
          disabled={busy}
          title="Refresh rekomendasi"
        >
          {busy ? "Memuat…" : "Refresh"}
        </button>
      </div>

      {busy && items.length === 0 && (
        <div className="text-sm text-gray-500 mb-2">Memuat…</div>
      )}

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
