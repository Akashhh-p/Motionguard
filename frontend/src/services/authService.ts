import { api } from "./api";
import { firebaseForgotPassword, firebaseGoogleLogin, firebaseLogin, firebaseLogout, firebaseResetPassword, firebaseSignup, firebaseVerifyEmail } from "./firebase";


export type User = {
  id: number;
  firebase_uid?: string;
  full_name: string;
  email: string;
  auth_provider: string;
  role: string;
  email_verified: boolean;
  profile_picture?: string;
};


function authError(error: any): Error {
  const code = error?.code || "";
  const messages: Record<string, string> = {
    "auth/email-already-in-use": "Email is already in use.",
    "auth/invalid-email": "Invalid email address.",
    "auth/weak-password": "Password is too weak.",
    "auth/user-not-found": "No account exists for this email.",
    "auth/wrong-password": "Incorrect password.",
    "auth/invalid-credential": "Invalid email or password.",
    "auth/popup-closed-by-user": "Google sign-in was closed before completion.",
    "auth/network-request-failed": "Network error. Check your connection.",
    "auth/configuration-not-found": "Firebase authentication is not configured for this project."
  };
  return new Error(messages[code] || error?.message || "Authentication failed.");
}


export async function syncSession() {
  const { data } = await api.post<User>("/auth/session", {});
  localStorage.setItem("motionguard_user", JSON.stringify(data));
  return data;
}


export async function signup(full_name: string, email: string, password: string) {
  try {
    await firebaseSignup(full_name, email, password);
    return await syncSession();
  } catch (error) {
    throw authError(error);
  }
}


export async function login(email: string, password: string) {
  try {
    await firebaseLogin(email, password);
    return await syncSession();
  } catch (error) {
    throw authError(error);
  }
}


export async function googleLogin() {
  try {
    await firebaseGoogleLogin();
    return await syncSession();
  } catch (error) {
    throw authError(error);
  }
}


export async function forgotPassword(email: string) {
  try {
    await firebaseForgotPassword(email);
    return { message: "Password reset email sent. Check your inbox." };
  } catch (error) {
    throw authError(error);
  }
}


export async function resetPassword(token: string, password: string) {
  try {
    await firebaseResetPassword(token, password);
    return { message: "Password reset successfully." };
  } catch (error) {
    throw authError(error);
  }
}


export async function verifyEmail(token: string) {
  try {
    await firebaseVerifyEmail(token);
    return { message: "Email verified successfully." };
  } catch (error) {
    throw authError(error);
  }
}


export async function logout() {
  await api.post("/auth/logout", {}).catch(() => undefined);
  await firebaseLogout();
  localStorage.removeItem("motionguard_user");
}


export async function me() {
  const { data } = await api.get<User>("/auth/me");
  localStorage.setItem("motionguard_user", JSON.stringify(data));
  return data;
}
