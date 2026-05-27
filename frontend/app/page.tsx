"use client";

import { useEffect, useRef, useState } from "react";
import { v4 as uuidv4 } from "uuid";

import ChatInput from "@/components/ChatInput";
import DenominationSelector from "@/components/DenominationSelector";
import MessageBubble from "@/components/MessageBubble";
import { Denomination, Message, sendMessage } from "@/lib/api";

export default function Home() {
  const [sessionId] = useState(() => uuidv4());
  const [denomination, setDenomination] = useState<Denomination>("protestant");
  const [messages, setMessages] = useState<Message[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  async function handleSend(text: string) {
    setError(null);
    const userMsg: Message = { role: "user", content: text };
    setMessages((prev) => [...prev, userMsg]);
    setLoading(true);

    try {
      const resp = await sendMessage(sessionId, text, denomination);
      const assistantMsg: Message = {
        role: "assistant",
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
    <div className="min-h-screen bg-stone-50 flex flex-col">
      {/* Header */}
      <header className="bg-amber-800 text-white px-6 py-4 shadow-md">
        <div className="max-w-3xl mx-auto flex items-center justify-between flex-wrap gap-3">
          <div>
            <h1 className="text-xl font-bold tracking-tight">✝ Christianity AI Assistant</h1>
            <p className="text-amber-200 text-xs mt-0.5">
              Scripture-grounded · Denomination-aware · Hallucination-resistant
            </p>
          </div>
          <DenominationSelector
            value={denomination}
            onChange={setDenomination}
            disabled={loading}
          />
        </div>
      </header>

      {/* Messages */}
      <main className="flex-1 overflow-y-auto px-4 py-6">
        <div className="max-w-3xl mx-auto space-y-4">
          {messages.length === 0 && (
            <div className="text-center text-gray-400 text-sm mt-16 space-y-2">
              <p className="text-4xl">✝</p>
              <p className="font-medium text-gray-500">Ask about scripture, theology, or Christian life.</p>
              <p>Try: <span className="italic">&quot;What does the Bible say about forgiveness?&quot;</span></p>
              <p>Or: <span className="italic">&quot;Generate an image of the nativity scene.&quot;</span></p>
            </div>
          )}

          {messages.map((msg, i) => (
            <MessageBubble key={i} message={msg} />
          ))}

          {loading && (
            <div className="flex justify-start">
              <div className="bg-white border border-gray-100 rounded-2xl rounded-bl-sm px-4 py-3 shadow-sm">
                <div className="flex gap-1 items-center">
                  <span className="w-2 h-2 rounded-full bg-amber-400 animate-bounce [animation-delay:-0.3s]" />
                  <span className="w-2 h-2 rounded-full bg-amber-400 animate-bounce [animation-delay:-0.15s]" />
                  <span className="w-2 h-2 rounded-full bg-amber-400 animate-bounce" />
                </div>
              </div>
            </div>
          )}

          {error && (
            <div className="bg-red-50 border border-red-200 text-red-700 text-sm rounded-xl px-4 py-3">
              ⚠ {error}
            </div>
          )}

          <div ref={bottomRef} />
        </div>
      </main>

      {/* Input */}
      <footer className="border-t border-gray-200 bg-white px-4 py-4">
        <div className="max-w-3xl mx-auto">
          <ChatInput onSend={handleSend} disabled={loading} />
          <p className="text-xs text-gray-400 mt-2 text-center">
            Responses grounded in KJV scripture · Citations verified · Denomination: {denomination}
          </p>
        </div>
      </footer>
    </div>
  );
}
