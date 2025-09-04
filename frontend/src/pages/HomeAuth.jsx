import React, { useEffect, useState } from "react";
import { api } from "../api";
import PlaceCard from "../components/PlaceCard";

export default function HomeAuth() {
  const [items, setItems] = useState([]);
  const [need, setNeed] = useState(false);
  const [msg, setMsg] = useState("");

  useEffect(() => {
    api.get("/api/recs/hybrid?k=12")
      .then((res) => setItems(res.data || []))
      .catch((err) => {
        if (err?.response?.status === 428) {
          setNeed(true);
          setMsg(err?.response?.data?.message || "Silakan onboarding dulu.");
        }
      });
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
      <h1 className="text-xl font-semibold mb-4">Rekomendasi AI (Hybrid)</h1>
      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-4">
        {items.map((p) => (
          <PlaceCard key={p.place_id ?? p.id} p={p} />
        ))}
      </div>
    </div>
  );
}
