import { Message } from "@/lib/api";
import CitationBadge from "./CitationBadge";

interface Props {
  message: Message;
}

export default function MessageBubble({ message }: Props) {
  const isUser = message.role === "user";

  return (
    <div className={`flex ${isUser ? "justify-end" : "justify-start"}`}>
      <div
        className={`max-w-[80%] rounded-2xl px-4 py-3 shadow-sm
          ${isUser
            ? "bg-amber-700 text-white rounded-br-sm"
            : message.flagged
              ? "bg-red-50 text-red-800 border border-red-200 rounded-bl-sm"
              : "bg-white text-gray-800 border border-gray-100 rounded-bl-sm"
          }`}
      >
        {message.flagged && (
          <p className="text-xs font-semibold text-red-600 mb-1">🚫 Request blocked</p>
        )}

        {message.intent && !isUser && (
          <p className="text-xs text-gray-400 mb-1 font-mono">
            [{message.intent}]
          </p>
        )}

        <p className="whitespace-pre-wrap leading-relaxed text-sm">{message.content}</p>

        {message.image_url && (
          <div className="mt-3">
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img
              src={message.image_url}
              alt="Generated Christian artwork"
              className="rounded-lg max-w-full border border-gray-200"
            />
          </div>
        )}

        {!isUser && (
          <CitationBadge
            citations={message.citations ?? []}
            hallucinated={message.hallucinated_refs ?? []}
            driftWarning={message.drift_warning ?? false}
          />
        )}
      </div>
    </div>
  );
}
