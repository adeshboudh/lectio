"use client";

import { FormEvent, useRef } from "react";

interface Props {
  onSend: (text: string) => void;
  disabled?: boolean;
}

export default function ChatInput({ onSend, disabled }: Props) {
  const ref = useRef<HTMLTextAreaElement>(null);

  function handleSubmit(e: FormEvent) {
    e.preventDefault();
    const text = ref.current?.value.trim();
    if (!text) return;
    onSend(text);
    if (ref.current) ref.current.value = "";
  }

  function handleKeyDown(e: React.KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e as unknown as FormEvent);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="flex gap-2 items-end">
      <textarea
        ref={ref}
        rows={2}
        disabled={disabled}
        placeholder="Ask a question about Christianity, request a verse, or type 'generate an image of…'"
        onKeyDown={handleKeyDown}
        className="flex-1 resize-none rounded-xl border border-gray-300 px-4 py-2.5 text-sm
          focus:outline-none focus:ring-2 focus:ring-amber-500 focus:border-transparent
          disabled:bg-gray-50 disabled:text-gray-400"
      />
      <button
        type="submit"
        disabled={disabled}
        className="px-4 py-2.5 rounded-xl bg-amber-700 text-white text-sm font-medium
          hover:bg-amber-800 active:scale-95 transition-all
          disabled:opacity-50 disabled:cursor-not-allowed"
      >
        Send
      </button>
    </form>
  );
}
