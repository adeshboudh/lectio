"use client";

import { IcBook, IcDove, IcColumns, IcImage, IcFlame } from "./Icons";

const SUGGESTIONS = [
  {
    cat: "Scripture",
    Icon: IcBook,
    q: "What does Scripture say about finding peace in times of anxiety?",
    hint: "Verses on stillness & trust",
  },
  {
    cat: "Theology",
    Icon: IcDove,
    q: "Explain the doctrine of grace and how it relates to faith.",
    hint: "Doctrine, plainly explained",
  },
  {
    cat: "Church History",
    Icon: IcColumns,
    q: "Why was the Council of Nicaea convened in 325 AD?",
    hint: "Councils, fathers & creeds",
  },
  {
    cat: "Sacred Art",
    Icon: IcImage,
    q: "Create an illuminated manuscript page depicting the Good Shepherd.",
    hint: "Generate Christian artwork",
  },
];

interface Props {
  onPick: (text: string) => void;
}

export default function EmptyState({ onPick }: Props) {
  return (
    <div className="empty">
      <div className="empty-mark">
        <IcFlame size={30} sw={1.5} />
      </div>
      <h1 className="empty-greeting">
        Peace be with you.<br />What shall we <em>study</em> today?
      </h1>
      <p className="empty-sub">
        Ask about Scripture, theology, or the history of the Church. Every citation is
        drawn from a verified corpus — references that cannot be confirmed are marked,
        never invented.
      </p>
      <div className="suggest-grid">
        {SUGGESTIONS.map((s) => (
          <button key={s.cat} className="suggest" onClick={() => onPick(s.q)}>
            <span className="suggest-cat">
              <s.Icon /> {s.cat}
            </span>
            <span className="suggest-q">{s.q}</span>
            <span className="suggest-hint">{s.hint}</span>
          </button>
        ))}
      </div>
    </div>
  );
}
