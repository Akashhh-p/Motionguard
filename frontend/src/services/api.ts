import axios from "axios";
import { getFirebaseIdToken } from "./firebase";

export const api = axios.create({
  baseURL: import.meta.env.DEV ? "/api" : import.meta.env.VITE_API_URL || "/api"
});

api.interceptors.request.use(async (config) => {
  const token = await getFirebaseIdToken();
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem("motionguard_user");
      if (!window.location.pathname.includes("/login")) window.location.href = "/login";
    }
    return Promise.reject(error);
  }
);

export function fileUrl(path: string) {
  return `${api.defaults.baseURL}${path}`;
}
