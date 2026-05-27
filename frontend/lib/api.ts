export type Denomination = "protestant" | "catholic" | "orthodox";

export interface Citation {
  ref: string;
  book: string;
  chapter: number;
  verse: number;
}

export interface ChatResponse {
  session_id: string;
  request_id: string;
  response: string;
  citations: Citation[];
  hallucinated_refs: string[];
  flagged: boolean;
  drift_warning: boolean;
  intent: string;
  latency_ms: Record<string, number>;
  image_url: string;
}

export interface Message {
  role: "user" | "assistant";
  content: string;
  citations?: Citation[];
  hallucinated_refs?: string[];
  drift_warning?: boolean;
  flagged?: boolean;
  intent?: string;
  image_url?: string;
}

const BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export async function sendMessage(
  session_id: string,
  message: string,
  denomination: Denomination
): Promise<ChatResponse> {
  const res = await fetch(`${BASE_URL}/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ session_id, message, denomination }),
  });
  if (!res.ok) {
    const err = await res.text();
    throw new Error(`API error ${res.status}: ${err}`);
  }
  return res.json();
}
