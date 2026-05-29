import { Citation } from "@/lib/api";
import { IcCheckSeal, IcSlash } from "./Icons";

export function VerifiedTick() {
  return (
    <span className="verified-tick">
      <IcCheckSeal size={13} sw={1.6} /> Verified
    </span>
  );
}

interface VerseBlockProps {
  citation: Citation;
  index?: number;
  variant?: "marginalia" | "card" | "footnote";
}

export function VerseBlock({ citation, index, variant = "marginalia" }: VerseBlockProps) {
  if (variant === "card") {
    return (
      <div className="cite-card">
        <div className="cite-card-head">
          <span className="verse-ref">{citation.ref}</span>
          <span style={{ marginLeft: "auto" }}>
            <VerifiedTick />
          </span>
        </div>
        <div className="cite-card-body">
          <span className="verse-ref verse-version">KJV · verified corpus</span>
        </div>
      </div>
    );
  }

  if (variant === "footnote") {
    return (
      <div className="footnote">
        {index !== undefined && (
          <span className="footnote-num">{index + 1}</span>
        )}
        <div style={{ display: "flex", alignItems: "center", gap: 10, flexWrap: "wrap" }}>
          <span className="verse-ref">{citation.ref}</span>
          <span className="verse-ref verse-version">· KJV</span>
          <VerifiedTick />
        </div>
      </div>
    );
  }

  // marginalia (default)
  return (
    <div className="cite-marginalia">
      <span className="verse-ref">{citation.ref}</span>
      <span className="verse-ref verse-version">· KJV</span>
      <VerifiedTick />
    </div>
  );
}

interface RedactedRefProps {
  label: string;
}

export function RedactedRef({ label }: RedactedRefProps) {
  return (
    <div className="redacted">
      <span className="redacted-ref">{label}</span>
      <span className="redacted-note">
        <IcSlash size={13} sw={1.7} /> not in verified corpus
      </span>
    </div>
  );
}

interface CitationsBlockProps {
  citations: Citation[];
  hallucinated: string[];
  variant?: "marginalia" | "card" | "footnote";
}

export function CitationsBlock({ citations, hallucinated, variant = "marginalia" }: CitationsBlockProps) {
  if (!citations.length && !hallucinated.length) return null;

  if (variant === "footnote") {
    return (
      <>
        {hallucinated.map((r) => <RedactedRef key={r} label={r} />)}
        {citations.length > 0 && (
          <div className="footnotes">
            <div className="footnotes-label">Citations · verified corpus</div>
            {citations.map((c, i) => (
              <VerseBlock key={c.ref} citation={c} index={i} variant="footnote" />
            ))}
          </div>
        )}
      </>
    );
  }

  return (
    <div style={{ marginTop: 8 }}>
      {citations.map((c) => (
        <VerseBlock key={c.ref} citation={c} variant={variant} />
      ))}
      {hallucinated.map((r) => <RedactedRef key={r} label={r} />)}
    </div>
  );
}
