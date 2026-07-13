import { createContext, ReactNode, useContext, useMemo } from "react";
import { User } from "../services/authService";


type AuthContextValue = {
  user: User | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  signup: (name: string, email: string, password: string) => Promise<void>;
  continueWithGoogle: () => Promise<void>;
  logout: () => Promise<void>;
};


const AuthContext = createContext<AuthContextValue | null>(null);

const localUser: User = {
  id: 1,
  full_name: "MotionGuard Operator",
  email: "operator@motionguard.local",
  auth_provider: "local",
  role: "Operator",
  email_verified: true
};

export function AuthProvider({ children }: { children: ReactNode }) {
  const value = useMemo<AuthContextValue>(
    () => ({
      user: localUser,
      loading: false,
      login: async () => undefined,
      signup: async () => undefined,
      continueWithGoogle: async () => undefined,
      logout: async () => undefined
    }),
    []
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}


export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) throw new Error("useAuth must be used inside AuthProvider");
  return context;
}
