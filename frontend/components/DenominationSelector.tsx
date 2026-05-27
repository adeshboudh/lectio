"use client";

import { Denomination } from "@/lib/api";

const OPTIONS: { value: Denomination; label: string; description: string }[] = [
  { value: "protestant", label: "Protestant", description: "66-book canon, sola scriptura" },
  { value: "catholic", label: "Catholic", description: "73-book canon, Scripture + Tradition" },
  { value: "orthodox", label: "Orthodox", description: "Wider canon, Holy Tradition" },
];

interface Props {
  value: Denomination;
  onChange: (d: Denomination) => void;
  disabled?: boolean;
}

export default function DenominationSelector({ value, onChange, disabled }: Props) {
  return (
    <div className="flex gap-2 flex-wrap">
      {OPTIONS.map((opt) => (
        <button
          key={opt.value}
          onClick={() => onChange(opt.value)}
          disabled={disabled}
          title={opt.description}
          className={`px-3 py-1.5 rounded-full text-sm font-medium border transition-colors
            ${value === opt.value
              ? "bg-amber-700 text-white border-amber-700"
              : "bg-white text-gray-700 border-gray-300 hover:border-amber-600 hover:text-amber-700"
            }
            disabled:opacity-50 disabled:cursor-not-allowed`}
        >
          {opt.label}
        </button>
      ))}
    </div>
  );
}
