"use client";

import { useEffect, useRef, useState } from "react";
import { v4 as uuidv4 } from "uuid";
import { Denomination, Message, sendMessage } from "@/lib/api";
import DenominationSelector from "@/components/DenominationSelector";
import MessageBubble from "@/components/MessageBubble";
import EmptyState from "@/components/EmptyState";
import Loading from "@/components/Loading";
import Composer from "@/components/Composer";
import { IcFlame, IcPlus, IcMoon, IcSun } from "@/components/Icons";

export default function Home() {
  const [sessionId] = useState(() => uuidv4());
  const [denomination, setDenomination] = useState<Denomination>("protestant");
  const [theme, setTheme] = useState<"light" | "dark">("light");
  const [messages, setMessages] = useState<Message[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const scrollRef = useRef<HTMLDivElement>(null);

  // restore persisted prefs
  useEffect(() => {
    const savedTheme = localStorage.getItem("lectio.theme") as "light" | "dark" | null;
    if (savedTheme) setTheme(savedTheme);
    const savedDenom = localStorage.getItem("lectio.denom") as Denomination | null;
    if (savedDenom) setDenomination(savedDenom);
  }, []);

  // apply data-theme + data-denom to html/body (CSS selector hooks)
  useEffect(() => {
    document.documentElement.setAttribute("data-theme", theme);
    document.body.setAttribute("data-theme", theme);
    localStorage.setItem("lectio.theme", theme);
  }, [theme]);

  useEffect(() => {
    document.documentElement.setAttribute("data-denom", denomination);
    document.body.setAttribute("data-denom", denomination);
    localStorage.setItem("lectio.denom", denomination);
  }, [denomination]);

  // auto-scroll on new messages
  useEffect(() => {
    const el = scrollRef.current;
    if (!el) return;
    requestAnimationFrame(() => { el.scrollTop = el.scrollHeight; });
  }, [messages, loading]);

  async function handleSend(text: string) {
    setError(null);
    setMessages((prev) => [...prev, { role: "user", content: text }]);
    setLoading(true);
    try {
      const resp = await sendMessage(sessionId, text, denomination);
      const assistantMsg: Message = {
        role: "assistant",
        lens: denomination,
        content: resp.response,
        citations: resp.citations,
        hallucinated_refs: resp.hallucinated_refs,
        drift_warning: resp.drift_warning,
        flagged: resp.flagged,
        intent: resp.intent,
        image_url: resp.image_url,
      };
      setMessages((prev) => [...prev, assistantMsg]);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unknown error");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="app">
      <header className="header">
        <div className="brand">
          <span className="brand-mark">
            <IcFlame size={22} sw={1.5} />
          </span>
          <span className="brand-name">
            Lectio
            <span className="sub">Scripture Companion</span>
          </span>
        </div>

        <div className="header-spacer" />

        <DenominationSelector
          value={denomination}
          onChange={setDenomination}
          variant="cards"
          disabled={loading}
        />

        <button
          className="icon-btn"
          onClick={() => setMessages([])}
          aria-label="New conversation"
          title="New conversation"
        >
          <IcPlus />
        </button>
        <button
          className="icon-btn"
          onClick={() => setTheme((t) => (t === "light" ? "dark" : "light"))}
          aria-label="Toggle theme"
          title="Toggle candlelight"
        >
          {theme === "light" ? <IcMoon /> : <IcSun />}
        </button>
      </header>

      <div className="scroll" ref={scrollRef}>
        {messages.length === 0 && !loading ? (
          <EmptyState onPick={handleSend} />
        ) : (
          <div className="thread">
            {messages.map((msg, i) => (
              <MessageBubble key={i} message={msg} citeVariant="marginalia" />
            ))}
            {loading && <Loading />}
          </div>
        )}

        {error && (
          <div style={{ maxWidth: "var(--reading-width)", margin: "16px auto 0", padding: "0 clamp(16px,4vw,24px)" }}>
            <div className="blocked">
              <div>
                <div className="blocked-title" style={{ color: "var(--redacted)" }}>
                  Connection error
                </div>
                <div className="blocked-body">{error}</div>
              </div>
            </div>
          </div>
        )}
      </div>

      <Composer onSend={handleSend} disabled={loading} />
    </div>
  );
}
