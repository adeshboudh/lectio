import { Citation } from "@/lib/api";

interface Props {
  citations: Citation[];
  hallucinated: string[];
  driftWarning: boolean;
}

export default function CitationBadge({ citations, hallucinated, driftWarning }: Props) {
  if (!citations.length && !hallucinated.length && !driftWarning) return null;

  return (
    <div className="mt-2 space-y-1">
      {citations.length > 0 && (
        <div className="flex flex-wrap gap-1">
          {citations.map((c) => (
            <span
              key={c.ref}
              className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-amber-100 text-amber-800 border border-amber-200"
              title="Verified citation"
            >
              📖 {c.ref}
            </span>
          ))}
        </div>
      )}
      {hallucinated.length > 0 && (
        <div className="flex flex-wrap gap-1">
          {hallucinated.map((ref) => (
            <span
              key={ref}
              className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-red-100 text-red-700 border border-red-200"
              title="Reference not found in verified corpus — removed from response"
            >
              ⚠ {ref} (unverified)
            </span>
          ))}
        </div>
      )}
      {driftWarning && (
        <p className="text-xs text-orange-600 italic">
          ⚠ Some wording may not precisely reflect retrieved scripture. Verify directly.
        </p>
      )}
    </div>
  );
}
