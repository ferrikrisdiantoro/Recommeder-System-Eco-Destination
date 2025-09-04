import React from "react";

export default function SelectableCard({ item, selected, onToggle }) {
  return (
    <button
      type="button"
      onClick={() => onToggle?.(item)}
      className={`relative text-left bg-white rounded-xl shadow-sm border p-3
                  hover:shadow transition ${selected ? "ring-2 ring-teal-500" : ""}`}
    >
      <img
        src={item.image}
        alt={item.place_name || "Tempat"}
        className="w-full h-40 object-cover rounded-lg"
        loading="lazy"
      />
      <div className="mt-2 font-semibold line-clamp-2">{item.place_name}</div>
      <div className="text-sm text-gray-500">
        {item.city || "-"} • {item.category || "-"}
      </div>
      {selected && (
        <div className="absolute top-2 right-2 text-xs px-2 py-1 bg-teal-600 text-white rounded">
          Dipilih
        </div>
      )}
    </button>
  );
}
