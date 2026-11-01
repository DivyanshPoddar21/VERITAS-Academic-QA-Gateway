import { useId, useState } from "react";
import type { FormEvent, KeyboardEvent } from "react";

interface QuestionBoxProps {
  loading: boolean;
  onSubmit(question: string): void;
}

export function QuestionBox({
  loading,
  onSubmit,
}: QuestionBoxProps) {
  const id = useId();
  const [question, setQuestion] = useState("");
  const trimmedLength = question.trim().length;
  const canSubmit = !loading && trimmedLength >= 3 && trimmedLength <= 1000;

  function submitQuestion(): void {
    if (!canSubmit) {
      return;
    }

    onSubmit(question.trim());
  }

  function handleSubmit(event: FormEvent<HTMLFormElement>): void {
    event.preventDefault();
    submitQuestion();
  }

  function handleKeyDown(event: KeyboardEvent<HTMLTextAreaElement>): void {
    if (
      (event.ctrlKey || event.metaKey) &&
      event.key === "Enter" &&
      !event.nativeEvent.isComposing
    ) {
      event.preventDefault();
      submitQuestion();
    }
  }

  return (
    <section
      aria-labelledby={`${id}-title`}
      className="min-w-0 rounded-2xl border border-edge bg-panel p-5 sm:p-6"
    >
      <h2
        id={`${id}-title`}
        className="text-lg font-semibold text-slate-100"
      >
        Ask the course corpus
      </h2>
      <p className="mt-2 text-sm leading-6 text-slate-400">
        Ask a focused question about the material in your indexed PDFs.
      </p>

      <form
        onSubmit={handleSubmit}
        aria-busy={loading}
        className="mt-5"
      >
        <label
          htmlFor={`${id}-question`}
          className="block text-sm font-medium text-slate-200"
        >
          Your question
        </label>

        <textarea
          id={`${id}-question`}
          name="question"
          rows={5}
          minLength={3}
          maxLength={1000}
          required
          disabled={loading}
          value={question}
          onChange={(event) => setQuestion(event.currentTarget.value)}
          onKeyDown={handleKeyDown}
          aria-describedby={`${id}-help ${id}-counter`}
          placeholder="How does gradient descent update model parameters?"
          className="mt-2 block w-full min-w-0 resize-y rounded-xl border border-edge bg-ink px-4 py-3 text-base leading-7 text-slate-100 placeholder:text-slate-600 focus-visible:border-accent focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent disabled:cursor-wait disabled:opacity-60"
        />

        <div className="mt-3 flex flex-wrap items-center justify-between gap-x-4 gap-y-2 text-xs text-slate-400">
          <p id={`${id}-help`}>
            3–1000 characters · Ctrl/Cmd + Enter to submit
          </p>
          <p id={`${id}-counter`} className="shrink-0 font-mono">
            {question.length}/1000
          </p>
        </div>

        <div className="mt-5 flex justify-end">
          <button
            type="submit"
            disabled={!canSubmit}
            className="w-full rounded-lg bg-accent px-5 py-3 text-sm font-semibold text-ink transition-colors hover:bg-sky-300 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent focus-visible:ring-offset-2 focus-visible:ring-offset-panel disabled:cursor-not-allowed disabled:opacity-50 sm:w-auto"
          >
            {loading ? "Checking evidence" : "Submit"}
          </button>
        </div>
      </form>
    </section>
  );
}