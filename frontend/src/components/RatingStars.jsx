import React from "react";

/**
 * @param {{ value:number, onChange:(n:number)=>void }} props
 */
export default function RatingStars({ value = 0, onChange }) {
  return (
    <div className="flex gap-1" role="radiogroup" aria-label="Pilih rating">
      {[1, 2, 3, 4, 5].map((n) => {
        const active = Number(value) >= n;
        return (
          <button
            key={n}
            type="button"
            onClick={() => onChange?.(n)}
            aria-checked={active}
            role="radio"
            className={`w-7 h-7 rounded-full border flex items-center justify-center ${
              active ? "bg-yellow-400" : "bg-white"
            }`}
            title={`${n} bintang`}
          >
            {n}
          </button>
        );
      })}
    </div>
  );
}
