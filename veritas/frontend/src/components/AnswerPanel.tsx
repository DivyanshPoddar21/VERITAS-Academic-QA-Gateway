import { useId } from "react";
import type { ReactNode } from "react";

import type { QuestionResponse } from "../types/contracts";
import { CitationCard } from "./CitationCard";

interface AnswerPanelProps {
  data: QuestionResponse | null;
  loading: boolean;
  error: string | null;
}

export function AnswerPanel({
  data,
  loading,
  error,
}: AnswerPanelProps) {
  const id = useId();
  let content: ReactNode;

  if (loading) {
    content = (
      <div className="rounded-2xl border border-edge bg-panel p-5 sm:p-6">
        <h2
          id={`${id}-title`}
          className="text-lg font-semibold text-slate-200"
        >
          Checking the course corpus
        </h2>
        <p className="sr-only">
          Retrieving passages and checking their similarity to your question.
        </p>
        <div aria-hidden="true" className="mt-5 animate-pulse space-y-3">
          <div className="h-3 w-3/4 rounded bg-slate-700/60" />
          <div className="h-3 w-full rounded bg-slate-700/40" />
          <div className="h-3 w-5/6 rounded bg-slate-700/40" />
          <div className="h-3 w-2/3 rounded bg-slate-700/40" />
          <div className="mt-6 h-8 w-32 rounded bg-slate-700/40" />
        </div>
      </div>
    );
  } else if (error) {
    content = (
      <div className="rounded-2xl border border-red-500/40 bg-red-500/5 p-5 sm:p-6">
        <p className="text-xs font-semibold tracking-widest text-red-300 uppercase">
          Request error
        </p>
        <h2
          id={`${id}-title`}
          className="mt-2 text-lg font-semibold text-red-100"
        >
          Unable to complete the request
        </h2>
        <p className="mt-3 text-sm leading-7 text-red-200 [overflow-wrap:anywhere]">
          {error}
        </p>
      </div>
    );
  } else if (data?.status === "answered") {
    content = (
      <>
        <div className="rounded-2xl border border-emerald-500/35 bg-panel p-5 sm:p-6">
          <span className="inline-flex rounded-full border border-emerald-500/25 bg-emerald-500/10 px-3 py-1 text-xs font-medium text-emerald-300">
            Answered
          </span>

          <h2
            id={`${id}-title`}
            className="mt-4 text-lg font-semibold text-slate-100"
          >
            Answer
          </h2>

          <p className="mt-4 text-sm leading-8 whitespace-pre-wrap text-slate-200 [overflow-wrap:anywhere]">
            {data.answer}
          </p>

          <dl className="mt-6 flex flex-wrap gap-x-7 gap-y-4 border-t border-edge pt-4 text-xs">
            <div>
              <dt className="text-slate-500">Max similarity</dt>
              <dd className="mt-1 font-mono text-emerald-300">
                {data.max_score.toFixed(2)}
              </dd>
            </div>
            <div>
              <dt className="text-slate-500">Threshold</dt>
              <dd className="mt-1 font-mono text-slate-300">
                {data.threshold.toFixed(2)}
              </dd>
            </div>
            <div>
              <dt className="text-slate-500">Latency</dt>
              <dd className="mt-1 font-mono text-slate-300">
                {data.latency_ms.toFixed(2)} ms
              </dd>
            </div>
          </dl>
        </div>

        <section aria-labelledby={`${id}-sources`} className="mt-6 min-w-0">
          <div className="mb-3 flex items-center justify-between gap-3">
            <h3
              id={`${id}-sources`}
              className="text-sm font-semibold text-slate-200"
            >
              Sources
            </h3>
            <span className="text-xs text-slate-500">
              {data.citations.length}{" "}
              {data.citations.length === 1 ? "passage" : "passages"}
            </span>
          </div>

          <ol className="space-y-3">
            {data.citations.map((citation, index) => (
              <li key={citation.chunk_id} className="min-w-0">
                <CitationCard citation={citation} rank={index + 1} />
              </li>
            ))}
          </ol>
        </section>
      </>
    );
  } else if (data?.status === "refused") {
    content = (
      <div className="rounded-2xl border border-amber-500/40 bg-amber-500/5 p-5 sm:p-6">
        <span className="inline-flex rounded-full border border-amber-500/25 bg-amber-500/10 px-3 py-1 text-xs font-medium text-amber-300">
          Outside indexed material
        </span>

        <h2
          id={`${id}-title`}
          className="mt-4 text-lg font-semibold text-amber-100"
        >
          No supported answer
        </h2>

        <p className="mt-3 text-sm leading-7 text-amber-100/80 [overflow-wrap:anywhere]">
          {data.answer ||
            "This question falls outside the indexed course material."}
        </p>

        <div className="mt-5 rounded-lg border border-amber-500/20 bg-ink/50 px-4 py-3">
          <p className="text-xs text-amber-200/70">
            Maximum similarity &lt; required threshold
          </p>
          <p className="mt-2 font-mono text-base text-amber-300">
            {data.max_score.toFixed(2)} &lt; {data.threshold.toFixed(2)}
          </p>
        </div>

        <p className="mt-4 text-xs leading-6 text-slate-400">
          Try a question covered in the loaded course PDFs.
        </p>
      </div>
    );
  } else {
    content = (
      <div className="rounded-2xl border border-dashed border-edge bg-panel/40 px-5 py-9 text-center sm:px-6">
        <h2
          id={`${id}-title`}
          className="text-base font-medium text-slate-300"
        >
          Your answer and evidence will appear here
        </h2>
        <p className="mx-auto mt-3 max-w-md text-sm leading-7 text-slate-500">
          Submit a course question to see a response, retrieval scores,
          and page-level source passages.
        </p>
      </div>
    );
  }

  return (
    <section
      aria-labelledby={`${id}-title`}
      aria-live="polite"
      aria-busy={loading}
      className="min-w-0"
    >
      {content}
    </section>
  );
}