import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
} from "react";
import type { ReactElement, ReactNode } from "react";

import { login } from "../api/client";

export interface AuthContextValue {
  token: string | null;
  username: string | null;
  isAuthenticated: boolean;
  signIn(username: string, password: string): Promise<void>;
  signOut(): void;
}

interface AuthState {
  token: string | null;
  username: string | null;
}

interface AuthProviderProps {
  children: ReactNode;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

function readStoredAuth(): AuthState {
  try {
    return {
      token: window.localStorage.getItem("veritas_token"),
      username: window.localStorage.getItem("veritas_user"),
    };
  } catch {
    return { token: null, username: null };
  }
}

export function AuthProvider({
  children,
}: AuthProviderProps): ReactElement {
  const [auth, setAuth] = useState<AuthState>(readStoredAuth);

  const signIn = useCallback(
    async (username: string, password: string): Promise<void> => {
      const response = await login(username, password);

      try {
        window.localStorage.setItem("veritas_user", username);
      } catch {
        // Persistence is best-effort when browser storage is unavailable.
      }

      setAuth({
        token: response.access_token,
        username,
      });
    },
    [],
  );

  const signOut = useCallback((): void => {
    try {
      window.localStorage.removeItem("veritas_token");
      window.localStorage.removeItem("veritas_user");
    } catch {
      // Always clear React state, regardless of storage availability.
    }

    setAuth({ token: null, username: null });
  }, []);

  useEffect(() => {
    const handleUnauthorized = (): void => {
      signOut();
    };

    window.addEventListener("veritas:unauthorized", handleUnauthorized);

    return () => {
      window.removeEventListener(
        "veritas:unauthorized",
        handleUnauthorized,
      );
    };
  }, [signOut]);

  const value = useMemo<AuthContextValue>(
    () => ({
      token: auth.token,
      username: auth.username,
      isAuthenticated: Boolean(auth.token),
      signIn,
      signOut,
    }),
    [auth.token, auth.username, signIn, signOut],
  );

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthContextValue {
  const context = useContext(AuthContext);

  if (context === undefined) {
    throw new Error("useAuth must be used within an AuthProvider.");
  }

  return context;
}