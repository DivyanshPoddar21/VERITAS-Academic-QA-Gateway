import axios from "axios";
import type { AxiosResponse } from "axios";

import type {
  QuestionRequest,
  QuestionResponse,
  TokenResponse,
} from "../types/contracts";

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL ?? "http://localhost:8000",
  timeout: 30000,
});

api.interceptors.request.use((config) => {
  try {
    const token = window.localStorage.getItem("veritas_token");
    if (token) {
      config.headers.set("Authorization", `Bearer ${token}`);
    }
  } catch {
    // Browser storage may be unavailable.
  }

  return config;
});

api.interceptors.response.use(
  (response) => response,
  (error: unknown): Promise<never> => {
    if (
      axios.isAxiosError<unknown>(error) &&
      error.response?.status === 401
    ) {
      try {
        window.localStorage.removeItem("veritas_token");
        window.localStorage.removeItem("veritas_user");
      } catch {
        // Still notify the auth provider when storage is unavailable.
      }

      window.dispatchEvent(new CustomEvent("veritas:unauthorized"));
    }

    return Promise.reject(error);
  },
);

export async function login(
  username: string,
  password: string,
): Promise<TokenResponse> {
  const body = new URLSearchParams({ username, password });

  const response = await api.post<
    TokenResponse,
    AxiosResponse<TokenResponse>,
    URLSearchParams
  >("/auth/login", body, {
    headers: {
      "Content-Type": "application/x-www-form-urlencoded",
    },
  });

  try {
    window.localStorage.setItem(
      "veritas_token",
      response.data.access_token,
    );
  } catch {
    // Persistence is best-effort when browser storage is unavailable.
  }

  return response.data;
}

export async function askQuestion(
  req: QuestionRequest,
): Promise<QuestionResponse> {
  const response = await api.post<
    QuestionResponse,
    AxiosResponse<QuestionResponse>,
    QuestionRequest
  >("/ask", req);

  return response.data;
}