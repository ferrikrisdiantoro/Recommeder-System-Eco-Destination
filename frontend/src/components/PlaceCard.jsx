import React from "react";
import { Link } from "react-router-dom";
import { asPriceText, formatRating } from "../utils/format";

/**
 * @param {{
 *   p: {
 *     id?: number|string,
 *     place_id?: number|string,
 *     image?: string,
 *     place_name?: string,
 *     city?: string,
 *     category?: string,
 *     price?: number|string|null,
 *     price_text?: string|null,
 *     rating?: number|string|null,
 *     map_url?: string
 *   },
 *   onBookmark?: (p:any)=>void
 * }} props
 */
export default function PlaceCard({ p, onBookmark }) {
  const pid = p.place_id ?? p.id;
  const imgAlt = p.place_name ? `Foto ${p.place_name}` : "Foto tempat";
  const priceText = p.price_text ?? asPriceText(p.price);

  return (
    <div className="bg-white rounded-xl shadow-sm p-3 flex flex-col">
      <img
        src={p.image}
        alt={imgAlt}
        className="w-full h-44 object-cover rounded-lg"
        loading="lazy"
      />

      <div className="mt-3 flex-1">
        <h3 className="font-semibold line-clamp-2">{p.place_name}</h3>
        <div className="text-sm text-gray-500">
          {p.city || "-"} • {p.category || "-"}
        </div>

        <div className="text-sm mt-2">
          Harga: <span className="font-medium">{priceText}</span>
        </div>

        <div className="text-sm">
          Rating: <span className="font-medium">{formatRating(p.rating)}</span>
        </div>
      </div>

      <div className="flex items-center gap-2 mt-3">
        <Link
          to={`/place/${pid}`}
          className="px-3 py-1 rounded-md bg-black text-white text-sm"
        >
          Detail
        </Link>

        {onBookmark && (
          <button
            type="button"
            onClick={() => onBookmark(p)}
            className="px-3 py-1 rounded-md border text-sm"
          >
            Bookmark
          </button>
        )}

        {p.map_url && (
          <a
            href={p.map_url}
            target="_blank"
            rel="noopener noreferrer"
            className="px-3 py-1 rounded-md border text-sm"
          >
            Map
          </a>
        )}
      </div>
    </div>
  );
}
