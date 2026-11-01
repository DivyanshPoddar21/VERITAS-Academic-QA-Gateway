import { useId } from "react";

interface ControlPanelProps {
  topK: number;
  threshold: number;
  onTopKChange(v: number): void;
  onThresholdChange(v: number): void;
}

export function ControlPanel({
  topK,
  threshold,
  onTopKChange,
  onThresholdChange,
}: ControlPanelProps) {
  const id = useId();

  return (
    <section
      aria-labelledby={`${id}-title`}
      className="min-w-0 rounded-2xl border border-edge bg-panel p-5"
    >
      <p className="text-xs font-semibold tracking-widest text-accent uppercase">
        Retrieval settings
      </p>
      <h2
        id={`${id}-title`}
        className="mt-2 text-lg font-semibold text-slate-100"
      >
        Evidence controls
      </h2>

      <div className="mt-6 space-y-7">
        <div>
          <div className="flex items-center justify-between gap-3">
            <label
              htmlFor={`${id}-top-k`}
              className="text-sm font-medium text-slate-200"
            >
              Top-k passages
            </label>
            <output
              htmlFor={`${id}-top-k`}
              className="rounded-md border border-edge bg-ink px-2 py-1 font-mono text-sm text-accent"
            >
              {topK}
            </output>
          </div>

          <input
            id={`${id}-top-k`}
            type="range"
            min={1}
            max={10}
            step={1}
            value={topK}
            onChange={(event) =>
              onTopKChange(Number(event.currentTarget.value))
            }
            aria-describedby={`${id}-top-k-help`}
            className="mt-4 block w-full cursor-pointer accent-accent focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent focus-visible:ring-offset-4 focus-visible:ring-offset-panel"
          />

          <p
            id={`${id}-top-k-help`}
            className="mt-3 text-xs leading-5 text-slate-400"
          >
            How many passages to retrieve
          </p>
        </div>

        <div className="border-t border-edge pt-6">
          <div className="flex items-center justify-between gap-3">
            <label
              htmlFor={`${id}-threshold`}
              className="text-sm font-medium text-slate-200"
            >
              Threshold τ
            </label>
            <output
              htmlFor={`${id}-threshold`}
              className="rounded-md border border-edge bg-ink px-2 py-1 font-mono text-sm text-accent"
            >
              {threshold.toFixed(2)}
            </output>
          </div>

          <input
            id={`${id}-threshold`}
            type="range"
            min={0.20}
            max={0.95}
            step={0.01}
            value={threshold}
            onChange={(event) =>
              onThresholdChange(Number(event.currentTarget.value))
            }
            aria-describedby={`${id}-threshold-help`}
            className="mt-4 block w-full cursor-pointer accent-accent focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent focus-visible:ring-offset-4 focus-visible:ring-offset-panel"
          />

          <p
            id={`${id}-threshold-help`}
            className="mt-3 text-xs leading-5 text-slate-400"
          >
            Minimum similarity required to answer
          </p>
        </div>
      </div>
    </section>
  );
}