import type { CSSProperties } from "react";

export type Status = "verified" | "configured" | "unverified" | "failed";

const FLAGS = ["blue", "white", "red", "green", "yellow"] as const;
const R = 40;
const CIRCUMFERENCE = 2 * Math.PI * R;

type SealProps = {
  /** Omit for the brand seal (five role colors). Pass [] while checks are loading. */
  statuses?: Status[];
  size?: number;
  animate?: boolean;
  label?: string;
};

export function Seal({ statuses, size = 48, animate = false, label }: SealProps) {
  const segments: string[] =
    statuses === undefined
      ? FLAGS.map((f) => `flag-${f}`)
      : statuses.length === 0
        ? Array.from({ length: 7 }, () => "pending")
        : statuses;
  const slot = CIRCUMFERENCE / segments.length;
  const gap = 4;
  const length = slot - gap;

  return (
    <svg
      className={animate ? "seal animate" : "seal"}
      width={size}
      height={size}
      viewBox="0 0 100 100"
      role="img"
      aria-label={label ?? "SunilAI seal"}
    >
      <g transform="rotate(-90 50 50)">
        {segments.map((cls, i) => (
          <circle
            key={i}
            className={`seg ${cls}`}
            cx="50"
            cy="50"
            r={R}
            fill="none"
            strokeDasharray={`${length} ${CIRCUMFERENCE - length}`}
            strokeDashoffset={-(i * slot + gap / 2)}
            style={{ "--i": i } as CSSProperties}
          />
        ))}
      </g>
      <circle cx="50" cy="50" r="27" className="seal-disc" />
      <text x="50" y="50" textAnchor="middle" dominantBaseline="central" className="seal-letter">
        S
      </text>
    </svg>
  );
}

/** A small stamp whose SHAPE (not only its color) says what the status is. */
export function Stamp({ status }: { status: Status }) {
  return (
    <svg className={`stamp ${status}`} width="30" height="30" viewBox="0 0 30 30" aria-hidden="true" focusable="false">
      {status === "verified" && (
        <>
          <circle cx="15" cy="15" r="13" className="fill" />
          <path d="M9 15.5l4 4 8-9" className="mark" />
        </>
      )}
      {status === "configured" && (
        <>
          <circle cx="15" cy="15" r="12" className="ring" />
          <path d="M15 3a12 12 0 010 24z" className="fill" />
        </>
      )}
      {status === "unverified" && <circle cx="15" cy="15" r="12" className="ring dashed" />}
      {status === "failed" && (
        <>
          <circle cx="15" cy="15" r="12" className="ring" />
          <path d="M10 10l10 10M20 10L10 20" className="mark" />
        </>
      )}
    </svg>
  );
}
