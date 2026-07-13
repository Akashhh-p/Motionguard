import axios from "axios";

function apiBaseURL() {
  const configured = import.meta.env.DEV ? "/api" : import.meta.env.VITE_API_URL || "/api";
  const trimmed = configured.replace(/\/+$/, "");

  if (trimmed.endsWith("/api")) {
    return trimmed;
  }

  return `${trimmed}/api`;
}

export const api = axios.create({
  baseURL: apiBaseURL()
});

api.interceptors.response.use(
  (response) => response,
  (error) => {
    return Promise.reject(error);
  }
);

export function fileUrl(path: string) {
  return `${api.defaults.baseURL}${path}`;
}
