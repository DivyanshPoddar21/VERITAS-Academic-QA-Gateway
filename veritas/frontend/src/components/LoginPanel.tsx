import axios from "axios";
import { useId, useState } from "react";
import type { FormEvent } from "react";

import { useAuth } from "../context/AuthContext";

export function LoginPanel() {
  const { signIn } = useAuth();
  const id = useId();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(
    event: FormEvent<HTMLFormElement>,
  ): Promise<void> {
    event.preventDefault();

    if (loading || !username.trim() || !password) {
      return;
    }

    setLoading(true);
    setError(null);

    try {
      await signIn(username.trim(), password);
    } catch (caught: unknown) {
      if (
        axios.isAxiosError<unknown>(caught) &&
        caught.response?.status === 401
      ) {
        setError("Incorrect username or password");
      } else {
        setError(
          "Unable to sign in. Check that the VERITAS server is running and try again.",
        );
      }
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="flex min-h-screen items-center justify-center bg-ink px-4 py-12 text-slate-200">
      <section
        aria-labelledby={`${id}-title`}
        className="w-full min-w-0 max-w-md rounded-2xl border border-edge bg-panel p-6 shadow-xl shadow-black/20 sm:p-8"
      >
        <div
          aria-hidden="true"
          className="mb-6 flex size-12 items-center justify-center rounded-xl border border-accent/30 bg-accent/10 text-xl font-semibold text-accent"
        >
          V
        </div>

        <p className="text-xs font-semibold tracking-widest text-accent uppercase">
          Academic access
        </p>
        <h1
          id={`${id}-title`}
          className="mt-2 text-2xl leading-snug font-semibold tracking-tight text-slate-100"
        >
          VERITAS — Academic QA Gateway
        </h1>
        <p className="mt-3 text-sm leading-6 text-slate-400">
          Sign in to ask questions against your indexed course material.
        </p>

        <form
          onSubmit={handleSubmit}
          aria-busy={loading}
          className="mt-8 space-y-5"
        >
          <div>
            <label
              htmlFor={`${id}-username`}
              className="block text-sm font-medium text-slate-200"
            >
              Username
            </label>
            <input
              id={`${id}-username`}
              name="username"
              type="text"
              autoComplete="username"
              autoCapitalize="none"
              spellCheck={false}
              required
              disabled={loading}
              value={username}
              onChange={(event) => setUsername(event.currentTarget.value)}
              aria-describedby={error ? `${id}-error` : undefined}
              className="mt-2 block w-full min-w-0 rounded-lg border border-edge bg-ink px-3 py-3 text-base text-slate-100 focus-visible:border-accent focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent disabled:opacity-60"
            />
          </div>

          <div>
            <label
              htmlFor={`${id}-password`}
              className="block text-sm font-medium text-slate-200"
            >
              Password
            </label>
            <input
              id={`${id}-password`}
              name="password"
              type="password"
              autoComplete="current-password"
              required
              disabled={loading}
              value={password}
              onChange={(event) => setPassword(event.currentTarget.value)}
              aria-describedby={error ? `${id}-error` : undefined}
              className="mt-2 block w-full min-w-0 rounded-lg border border-edge bg-ink px-3 py-3 text-base text-slate-100 focus-visible:border-accent focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent disabled:opacity-60"
            />
          </div>

          {error && (
            <p
              id={`${id}-error`}
              role="alert"
              className="rounded-lg border border-red-500/30 bg-red-500/10 px-3 py-3 text-sm leading-6 text-red-200"
            >
              {error}
            </p>
          )}

          <button
            type="submit"
            disabled={loading || !username.trim() || !password}
            className="w-full rounded-lg bg-accent px-4 py-3 text-sm font-semibold text-ink transition-colors hover:bg-sky-300 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent focus-visible:ring-offset-2 focus-visible:ring-offset-panel disabled:cursor-not-allowed disabled:opacity-50"
          >
            {loading ? "Signing in" : "Sign in"}
          </button>
        </form>

        <p className="mt-6 border-t border-edge pt-5 text-xs leading-5 text-slate-500">
          Course-based retrieval with page-level evidence.
        </p>
      </section>
    </main>
  );
}