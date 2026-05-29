"use client";

import { useLayoutEffect, useRef, useState } from "react";
import { IcSend, IcBook, IcImage, IcCheckSeal } from "./Icons";

interface Props {
  onSend: (text: string) => void;
  disabled?: boolean;
}

export default function Composer({ onSend, disabled }: Props) {
  const [val, setVal] = useState("");
  const [imageMode, setImageMode] = useState(false);
  const ta = useRef<HTMLTextAreaElement>(null);

  useLayoutEffect(() => {
    const el = ta.current;
    if (!el) return;
    el.style.height = "auto";
    el.style.height = Math.min(el.scrollHeight, 160) + "px";
  }, [val]);

  const submit = () => {
    const text = val.trim();
    if (!text || disabled) return;
    onSend(text);
    setVal("");
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      submit();
    }
  };

  return (
    <div className="composer-wrap">
      <div className="composer">
        <div className="mode-chips">
          <button
            className="mode-chip"
            data-active={String(!imageMode)}
            onClick={() => setImageMode(false)}
            disabled={disabled}
          >
            <IcBook /> Study
          </button>
          <button
            className="mode-chip"
            data-active={String(imageMode)}
            onClick={() => setImageMode(true)}
            disabled={disabled}
          >
            <IcImage /> Create art
          </button>
        </div>

        <div className="composer-box">
          <textarea
            ref={ta}
            rows={1}
            value={val}
            disabled={disabled}
            onChange={(e) => setVal(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={
              imageMode
                ? "Describe the sacred scene to create…"
                : "Ask about Scripture, theology, or church history…"
            }
          />
          <button
            className="send-btn"
            disabled={!val.trim() || disabled}
            onClick={submit}
            aria-label="Send"
          >
            <IcSend />
          </button>
        </div>

        <div className="composer-foot">
          <IcCheckSeal size={12} sw={1.6} />
          Citations verified against the KJV corpus
          <span className="dot">·</span>
          Denomination-aware responses
        </div>
      </div>
    </div>
  );
}
