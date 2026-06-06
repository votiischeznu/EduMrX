import axios from "axios";

const DataBaseURL = process.env.NEXT_PUBLIC_DataBaseURL;

export const API = axios.create({
  baseURL: DataBaseURL,
});

API.interceptors.request.use((config) => {
  const storedTokens = localStorage.getItem("tokens");

  if (storedTokens) {
    const tokens = JSON.parse(storedTokens);
    if (tokens?.access_token) {
      config.headers.Authorization = `Bearer ${tokens.access_token}`;
    }
  }

  if (config.data instanceof FormData) {
    delete config.headers["Content-Type"];
  } else {
    config.headers["Content-Type"] = "application/json";
  }

  return config;
});

API.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem("tokens");
      window.location.href = "/login";
    }
    return Promise.reject(error);
  },
);
