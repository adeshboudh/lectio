"use client";

import { useEffect, useRef, useState } from "react";
import { Denomination } from "@/lib/api";
import { CrossLatin, CrossCrucifix, CrossOrthodox, IcChevron, IcCheck } from "./Icons";

const DENOMS = {
  protestant: {
    name: "Protestant",
    lens: "Sola Scriptura",
    desc: "Answers grounded directly in Scripture, with emphasis on the plain reading of the Word.",
    swatch: "#1f3a5c",
    Icon: CrossLatin,
  },
  catholic: {
    name: "Catholic",
    lens: "Scripture & Tradition",
    desc: "Answers framed through Scripture alongside the Magisterium and the Church Fathers.",
    swatch: "#6e2a2a",
    Icon: CrossCrucifix,
  },
  orthodox: {
    name: "Orthodox",
    lens: "Holy Tradition",
    desc: "Answers shaped by the Fathers, the councils, and the liturgical life of the Church.",
    swatch: "#8a6516",
    Icon: CrossOrthodox,
  },
} as const;

const DENOM_ORDER: Denomination[] = ["protestant", "catholic", "orthodox"];

interface Props {
  value: Denomination;
  onChange: (d: Denomination) => void;
  variant?: "cards" | "segmented" | "minimal";
  disabled?: boolean;
}

export default function DenominationSelector({
  value,
  onChange,
  variant = "cards",
  disabled,
}: Props) {
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!open) return;
    const handle = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false);
    };
    document.addEventListener("mousedown", handle);
    return () => document.removeEventListener("mousedown", handle);
  }, [open]);

  if (variant === "segmented") {
    return (
      <div className="denom-seg">
        {DENOM_ORDER.map((id) => {
          const { name, Icon } = DENOMS[id];
          return (
            <button
              key={id}
              data-active={String(value === id)}
              onClick={() => onChange(id)}
              disabled={disabled}
              aria-label={name}
            >
              <Icon />
              <span className="seg-label">{name}</span>
            </button>
          );
        })}
      </div>
    );
  }

  if (variant === "minimal") {
    return (
      <div className="denom-min">
        {DENOM_ORDER.map((id) => {
          const { name, Icon } = DENOMS[id];
          return (
            <button
              key={id}
              data-active={String(value === id)}
              onClick={() => onChange(id)}
              disabled={disabled}
              aria-label={name}
            >
              <Icon />
              <span className="tip">{name}</span>
            </button>
          );
        })}
      </div>
    );
  }

  // cards (default) — popover
  const active = DENOMS[value];
  const ActiveIcon = active.Icon;

  return (
    <div className="denom-wrap" ref={ref}>
      <button
        className="denom-trigger"
        onClick={() => setOpen((o) => !o)}
        disabled={disabled}
        aria-haspopup="listbox"
        aria-expanded={open}
      >
        <span className="dt-sym">
          <ActiveIcon size={16} sw={1.7} />
        </span>
        <span style={{ textAlign: "left" }}>
          <span className="dt-lens">{active.lens}</span>
          <span className="dt-name">{active.name}</span>
        </span>
        <span className="chev">
          <IcChevron size={16} />
        </span>
      </button>

      {open && (
        <div className="denom-pop" role="listbox">
          <div className="denom-pop-title">Choose a reading lens</div>
          {DENOM_ORDER.map((id) => {
            const d = DENOMS[id];
            const DIcon = d.Icon;
            return (
              <button
                key={id}
                className="denom-opt"
                data-active={String(value === id)}
                role="option"
                aria-selected={value === id}
                onClick={() => { onChange(id); setOpen(false); }}
              >
                <span className="do-sym" style={{ background: d.swatch }}>
                  <DIcon size={20} sw={1.7} />
                </span>
                <span>
                  <span className="do-name">{d.name}</span>
                  <span className="do-desc">{d.desc}</span>
                </span>
                <span className="do-check"><IcCheck size={18} /></span>
              </button>
            );
          })}
        </div>
      )}
    </div>
  );
}
