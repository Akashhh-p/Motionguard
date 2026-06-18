import { createContext, ReactNode, useContext, useEffect, useMemo, useState } from "react";
import { login as loginApi, logout as logoutApi, me, signup as signupApi, googleLogin, syncSession, User } from "../services/authService";
import { observeFirebaseAuth } from "../services/firebase";


type AuthContextValue = {
  user: User | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  signup: (name: string, email: string, password: string) => Promise<void>;
  continueWithGoogle: () => Promise<void>;
  logout: () => Promise<void>;
};


const AuthContext = createContext<AuthContextValue | null>(null);


export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(() => {
    const raw = localStorage.getItem("motionguard_user");
    return raw ? JSON.parse(raw) : null;
  });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const unsubscribe = observeFirebaseAuth((firebaseUser) => {
      if (!firebaseUser) {
        localStorage.removeItem("motionguard_user");
        setUser(null);
        setLoading(false);
        return;
      }
      me()
        .then(setUser)
        .catch(() => syncSession().then(setUser).catch(() => setUser(null)))
        .finally(() => setLoading(false));
    });
    return unsubscribe;
  }, []);

  const value = useMemo<AuthContextValue>(
    () => ({
      user,
      loading,
      login: async (email, password) => setUser(await loginApi(email, password)),
      signup: async (name, email, password) => setUser(await signupApi(name, email, password)),
      continueWithGoogle: async () => setUser(await googleLogin()),
      logout: async () => {
        await logoutApi();
        setUser(null);
        window.location.href = "/login";
      }
    }),
    [user, loading]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}


export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) throw new Error("useAuth must be used inside AuthProvider");
  return context;
}
