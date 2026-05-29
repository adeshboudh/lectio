import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { Message } from "@/lib/api";
import { DENOM_ICON, CrossLatin, IcShieldSlash } from "./Icons";
import { CitationsBlock } from "./VerseBlock";

interface Props {
  message: Message;
  citeVariant?: "marginalia" | "card" | "footnote";
}

const DENOM_LENS: Record<string, string> = {
  protestant: "Protestant",
  catholic: "Catholic",
  orthodox: "Orthodox",
};

export default function MessageBubble({ message, citeVariant = "marginalia" }: Props) {
  if (message.role === "user") {
    return (
      <div className="msg msg-user">
        <div className="bubble-user">{message.content}</div>
      </div>
    );
  }

  const lens = message.lens ?? "protestant";
  const Sigil = DENOM_ICON[lens] ?? CrossLatin;
  const lensName = DENOM_LENS[lens] ?? "Protestant";

  const citations = message.citations ?? [];
  const hallucinated = message.hallucinated_refs ?? [];

  return (
    <div className="msg msg-assistant">
      <div className="assistant-head">
        <span className="assistant-sigil">
          <Sigil size={15} sw={1.7} />
        </span>
        Lectio
        <span className="lens-tag">
          through the <b>{lensName}</b> lens
        </span>
      </div>

      {message.flagged ? (
        <div className="blocked">
          <div className="blocked-icon">
            <IcShieldSlash size={18} sw={1.6} />
          </div>
          <div>
            <div className="blocked-title">This request can&apos;t be answered here</div>
            <div className="blocked-body">
              {message.content ||
                "Lectio is a study companion for Scripture, theology, and church history. " +
                "This message was set aside by the safety review. " +
                "You're welcome to rephrase — I'm glad to help with anything in the life of faith."}
            </div>
          </div>
        </div>
      ) : (
        <div className="prose">
          <ReactMarkdown remarkPlugins={[remarkGfm]}>{message.content}</ReactMarkdown>

          {message.image_url && (
            <figure className="artwork">
              <div className="artwork-frame">
                <div className="artwork-mat">
                  {/* eslint-disable-next-line @next/next/no-img-element */}
                  <img
                    src={message.image_url}
                    alt="Generated Christian artwork"
                    className="artwork-img"
                  />
                </div>
              </div>
              <figcaption className="artwork-cap">Generated Christian artwork</figcaption>
            </figure>
          )}

          <CitationsBlock
            citations={citations}
            hallucinated={hallucinated}
            variant={citeVariant}
          />
        </div>
      )}
    </div>
  );
}
