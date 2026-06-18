import { FirebaseApp, initializeApp } from "firebase/app";
import {
  Auth,
  browserLocalPersistence,
  applyActionCode,
  confirmPasswordReset,
  createUserWithEmailAndPassword,
  getAuth,
  GoogleAuthProvider,
  onAuthStateChanged,
  sendPasswordResetEmail,
  sendEmailVerification,
  setPersistence,
  signInWithEmailAndPassword,
  signInWithPopup,
  signOut,
  updateProfile,
  User as FirebaseUser
} from "firebase/auth";


const firebaseConfig = {
  apiKey: import.meta.env.VITE_FIREBASE_API_KEY,
  authDomain: import.meta.env.VITE_FIREBASE_AUTH_DOMAIN,
  projectId: import.meta.env.VITE_FIREBASE_PROJECT_ID,
  storageBucket: import.meta.env.VITE_FIREBASE_STORAGE_BUCKET,
  messagingSenderId: import.meta.env.VITE_FIREBASE_MESSAGING_SENDER_ID,
  appId: import.meta.env.VITE_FIREBASE_APP_ID
};


function missingFirebaseKeys() {
  return Object.entries(firebaseConfig).filter(([, value]) => !value).map(([key]) => key);
}


export function assertFirebaseConfigured() {
  const missing = missingFirebaseKeys();
  if (missing.length) {
    throw new Error(`Firebase config missing: ${missing.join(", ")}`);
  }
}


let firebaseApp: FirebaseApp | null = null;
let firebaseAuth: Auth | null = null;


export function getFirebaseAuth(): Auth {
  const missing = Object.entries(firebaseConfig).filter(([, value]) => !value).map(([key]) => key);
  if (missing.length) {
    throw new Error(`Firebase config missing: ${missing.join(", ")}`);
  }
  if (!firebaseApp) {
    firebaseApp = initializeApp(firebaseConfig);
    firebaseAuth = getAuth(firebaseApp);
    setPersistence(firebaseAuth, browserLocalPersistence);
  }
  return firebaseAuth!;
}


export async function getFirebaseIdToken(forceRefresh = false): Promise<string | null> {
  if (missingFirebaseKeys().length) return null;
  const user = getFirebaseAuth().currentUser;
  return user ? user.getIdToken(forceRefresh) : null;
}


export async function firebaseSignup(fullName: string, email: string, password: string) {
  assertFirebaseConfigured();
  const result = await createUserWithEmailAndPassword(getFirebaseAuth(), email, password);
  await updateProfile(result.user, { displayName: fullName });
  await sendEmailVerification(result.user);
  return result.user.getIdToken(true);
}


export async function firebaseLogin(email: string, password: string) {
  assertFirebaseConfigured();
  const result = await signInWithEmailAndPassword(getFirebaseAuth(), email, password);
  return result.user.getIdToken(true);
}


export async function firebaseGoogleLogin() {
  assertFirebaseConfigured();
  const provider = new GoogleAuthProvider();
  provider.setCustomParameters({ prompt: "select_account" });
  const result = await signInWithPopup(getFirebaseAuth(), provider);
  return result.user.getIdToken(true);
}


export function firebaseForgotPassword(email: string) {
  assertFirebaseConfigured();
  return sendPasswordResetEmail(getFirebaseAuth(), email);
}


export function firebaseResetPassword(code: string, password: string) {
  assertFirebaseConfigured();
  return confirmPasswordReset(getFirebaseAuth(), code, password);
}


export function firebaseVerifyEmail(code: string) {
  assertFirebaseConfigured();
  return applyActionCode(getFirebaseAuth(), code);
}


export function firebaseLogout() {
  if (missingFirebaseKeys().length) return Promise.resolve();
  return signOut(getFirebaseAuth());
}


export function observeFirebaseAuth(callback: (user: FirebaseUser | null) => void) {
  if (missingFirebaseKeys().length) {
    window.setTimeout(() => callback(null), 0);
    return () => undefined;
  }
  return onAuthStateChanged(getFirebaseAuth(), callback);
}
