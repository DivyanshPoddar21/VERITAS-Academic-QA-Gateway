import { useCallback, useEffect, useRef, useState } from "react";
import axios from "axios";

import { askQuestion } from "../api/client";
import type {
  QuestionRequest,
  QuestionResponse,
} from "../types/contracts";

interface UseAskResult {
  ask(req: QuestionRequest): Promise<void>;
  data: QuestionResponse | null;
  loading: boolean;
  error: string | null;
  reset(): void;
}

function validationMessages(body: unknown): string[] {
  if (
    typeof body !== "object" ||
    body === null ||
    !("detail" in body) ||
    !Array.isArray(body.detail)
  ) {
    return [];
  }

  return body.detail.flatMap((item: unknown): string[] => {
    if (
      typeof item === "object" &&
      item !== null &&
      "msg" in item &&
      typeof item.msg === "string"
    ) {
      return [item.msg];
    }

    return [];
  });
}

function readableError(error: unknown): string {
  if (axios.isAxiosError<unknown>(error)) {
    if (error.response?.status === 401) {
      return "Session expired. Please sign in again.";
    }

    if (error.response?.status === 422) {
      const messages = validationMessages(error.response.data);
      if (messages.length > 0) {
        return messages.join("; ");
      }
    }

    if (
      !error.response ||
      error.code === "ECONNABORTED" ||
      error.code === "ETIMEDOUT"
    ) {
      return "Cannot reach the VERITAS server.";
    }

    return error.message || "Unexpected error";
  }

  if (error instanceof Error) {
    return error.message || "Unexpected error";
  }

  return "Unexpected error";
}

export function useAsk(): UseAskResult {
  const [data, setData] = useState<QuestionResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const requestId = useRef(0);

  useEffect(() => {
    return () => {
      // Ignore pending results after this hook unmounts.
      requestId.current += 1;
    };
  }, []);

  const ask = useCallback(
    async (req: QuestionRequest): Promise<void> => {
      const currentId = ++requestId.current;

      setLoading(true);
      setError(null);
      setData(null);

      try {
        const result = await askQuestion(req);
        if (currentId === requestId.current) {
          setData(result);
        }
      } catch (caught: unknown) {
        if (currentId === requestId.current) {
          setError(readableError(caught));
        }
      } finally {
        if (currentId === requestId.current) {
          setLoading(false);
        }
      }
    },
    [],
  );

  const reset = useCallback((): void => {
    // A pending response must not repopulate state after reset.
    requestId.current += 1;
    setData(null);
    setError(null);
    setLoading(false);
  }, []);

  return { ask, data, loading, error, reset };
}