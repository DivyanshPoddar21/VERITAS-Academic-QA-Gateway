import { useId, useState } from "react";

import type { Citation } from "../types/contracts";

interface CitationCardProps {
  citation: Citation;
  rank: number;
}

export function CitationCard({
  citation,
  rank,
}: CitationCardProps) {
  const textId = useId();
  const [expanded, setExpanded] = useState(false);
  const similarity = (citation.score * 100).toFixed(1);

  return (
    <article className="min-w-0 rounded-xl border border-edge bg-panel p-4 sm:p-5">
      <div className="flex min-w-0 items-start gap-3">
        <span
          aria-label={`Source rank ${rank}`}
          className="flex size-7 shrink-0 items-center justify-center rounded-md border border-edge bg-ink font-mono text-xs text-slate-400"
        >
          {rank}
        </span>

        <h4 className="min-w-0 flex-1 text-sm leading-6 font-medium text-slate-200 [overflow-wrap:anywhere]">
          {citation.source} · p.{citation.page}
        </h4>

        <span
          aria-label={`Similarity ${similarity} percent`}
          title="Retrieval similarity"
          className="shrink-0 rounded-md border border-accent/20 bg-accent/10 px-2 py-1 font-mono text-xs text-accent"
        >
          {similarity}%
        </span>
      </div>

      <p
        id={textId}
        className={`mt-4 text-sm leading-7 whitespace-pre-wrap text-slate-400 [overflow-wrap:anywhere] ${
          expanded ? "" : "line-clamp-4"
        }`}
      >
        {citation.text}
      </p>

      <button
        type="button"
        aria-expanded={expanded}
        aria-controls={textId}
        onClick={() => setExpanded((current) => !current)}
        className="mt-3 rounded-md px-1 py-1 text-xs font-medium text-accent underline-offset-4 hover:underline focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent"
      >
        {expanded ? "Show less" : "Show more"}
      </button>
    </article>
  );
}