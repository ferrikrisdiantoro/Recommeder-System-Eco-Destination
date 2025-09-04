import React, { useState } from "react";

export default function Contact() {
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [msg, setMsg] = useState("");

  const submit = (e) => {
    e.preventDefault();
    alert("Terima kasih, pesan terkirim (dummy).");
    setName("");
    setEmail("");
    setMsg("");
  };

  return (
    <div className="max-w-xl">
      <h1 className="text-xl font-semibold mb-3">Contact</h1>

      <form onSubmit={submit} className="space-y-3">
        <input
          className="w-full border p-2 rounded"
          placeholder="Nama"
          value={name}
          onChange={(e) => setName(e.target.value)}
        />

        <input
          className="w-full border p-2 rounded"
          placeholder="Email"
          type="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
        />

        <textarea
          className="w-full border p-2 rounded"
          rows={5}
          placeholder="Pesan"
          value={msg}
          onChange={(e) => setMsg(e.target.value)}
        />

        <button type="submit" className="px-4 py-2 rounded bg-black text-white">
          Kirim
        </button>
      </form>
    </div>
  );
}
