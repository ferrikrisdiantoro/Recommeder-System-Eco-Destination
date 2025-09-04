// Util kecil biar tampilan aman & konsisten berbasis STRING

/**
 * Ubah input harga apa pun (string "Rp...", "10k", "-", atau number)
 * menjadi string siap-tayang. Prioritas:
 * 1) Jika sudah string "Rp..." atau "-" → pakai langsung
 * 2) Jika string lain (mis. "25k", "10.000") → pakai apa adanya
 * 3) Jika number > 0 → format jadi "Rp..."
 * 4) Lainnya → "-"
 */
export function asPriceText(value) {
  if (value === null || value === undefined || value === "") return "-";

  if (typeof value === "string") {
    const t = value.trim();
    if (t === "-" || t.toLowerCase().startsWith("rp")) return t;
    return t; // biarkan apa adanya (mis. "25k", "10.000")
  }

  const n = Number(value);
  if (!isFinite(n) || n <= 0) return "-";
  try {
    return new Intl.NumberFormat("id-ID", {
      style: "currency",
      currency: "IDR",
      maximumFractionDigits: 0,
    }).format(n);
  } catch {
    return String(value);
  }
}

export function formatRating(value) {
  const num = Number(value);
  if (!isFinite(num)) return "-";
  return num.toFixed(1);
}
