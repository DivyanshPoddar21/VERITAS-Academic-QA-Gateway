import { useEffect, useState } from "react";

import { AnswerPanel } from "./components/AnswerPanel";
import { ControlPanel } from "./components/ControlPanel";
import { LoginPanel } from "./components/LoginPanel";
import { QuestionBox } from "./components/QuestionBox";
import { useAuth } from "./context/AuthContext";
import { useAsk } from "./hooks/useAsk";

export default function App() {
  const { isAuthenticated, username, signOut } = useAuth();
  const { ask, data, loading, error, reset } = useAsk();
  const [topK, setTopK] = useState(5);
  const [threshold, setThreshold] = useState(0.35);

  useEffect(() => {
    if (!isAuthenticated) {
      reset();
    }
  }, [isAuthenticated, reset]);

  function handleSubmit(question: string): void {
    void ask({
      question,
      top_k: topK,
      threshold,
    });
  }

  if (!isAuthenticated) {
    return <LoginPanel />;
  }

  return (
    <div className="min-h-screen w-full bg-ink text-slate-200">
      <header className="border-b border-edge bg-panel">
        <div className="mx-auto flex w-full max-w-7xl flex-wrap items-center justify-between gap-4 px-4 py-5 sm:px-6 lg:px-8">
          <div className="min-w-0 flex-1 basis-64">
            <p className="text-xs font-semibold tracking-widest text-accent uppercase">
              Course evidence workspace
            </p>
            <h1 className="mt-2 text-xl leading-snug font-semibold tracking-tight text-slate-100 sm:text-2xl">
              VERITAS — Academic QA Gateway
            </h1>
          </div>

          <div className="flex min-w-0 max-w-full flex-wrap items-center gap-3">
            <span
              title={username ?? "User"}
              className="max-w-48 truncate text-sm text-slate-400"
            >
              Signed in as{" "}
              <strong className="font-medium text-slate-200">
                {username ?? "User"}
              </strong>
            </span>

            <button
              type="button"
              onClick={() => signOut()}
              className="shrink-0 rounded-lg border border-edge bg-ink px-3 py-2 text-sm font-medium text-slate-300 transition-colors hover:border-accent/50 hover:text-accent focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent"
            >
              Sign out
            </button>
          </div>
        </div>
      </header>

      <main className="mx-auto w-full max-w-7xl px-4 py-6 sm:px-6 sm:py-8 lg:px-8">
        <div className="grid min-w-0 grid-cols-1 items-start gap-6 lg:grid-cols-[18rem_minmax(0,1fr)]">
          <aside
            aria-label="Retrieval settings"
            className="min-w-0 space-y-4 lg:sticky lg:top-6"
          >
            <ControlPanel
              topK={topK}
              threshold={threshold}
              onTopKChange={setTopK}
              onThresholdChange={setThreshold}
            />

            <p className="px-1 text-xs leading-6 text-slate-500">
              Only indexed PDF passages are considered. Questions without
              sufficient similarity are refused before answer synthesis.
            </p>
          </aside>

          <div className="min-w-0 space-y-6">
            <QuestionBox loading={loading} onSubmit={handleSubmit} />
            <AnswerPanel data={data} loading={loading} error={error} />
          </div>
        </div>
      </main>
    </div>
  );
}