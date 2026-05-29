"use client";

import { useLayoutEffect, useRef, useState, useEffect } from "react";
import { IcSend, IcBook, IcImage, IcCheckSeal } from "./Icons";

const IMAGE_HINT = /\b(generate|create|draw|paint|show|image|picture|art|illustrate|depict)\b/i;

interface Props {
  onSend: (text: string) => void;
  disabled?: boolean;
}

export default function Composer({ onSend, disabled }: Props) {
  const [val, setVal] = useState("");
  const [imageMode, setImageMode] = useState(false);
  const [toast, setToast] = useState<string | null>(null);
  const toastTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const ta = useRef<HTMLTextAreaElement>(null);

  useLayoutEffect(() => {
    const el = ta.current;
    if (!el) return;
    el.style.height = "auto";
    el.style.height = Math.min(el.scrollHeight, 160) + "px";
  }, [val]);

  useEffect(() => {
    return () => { if (toastTimer.current) clearTimeout(toastTimer.current); };
  }, []);

  const showToast = (msg: string) => {
    setToast(msg);
    if (toastTimer.current) clearTimeout(toastTimer.current);
    toastTimer.current = setTimeout(() => setToast(null), 4000);
  };

  const submit = () => {
    const text = val.trim();
    if (!text || disabled) return;
    const looksLikeImage = IMAGE_HINT.test(text);
    if (!imageMode && looksLikeImage) {
      showToast("Looks like an image request — switch to Create Art mode?");
    } else if (imageMode && !looksLikeImage) {
      showToast("Looks like a scripture question — switch to Study mode?");
    }
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
      {toast && (
        <div className="composer-toast" role="status">
          {toast}
        </div>
      )}
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
