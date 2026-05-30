import { AuthAPI } from "./api"; // your axios file

export async function loginUser(phone: string, password: string) {
  const { data } = await AuthAPI.post("auth/login/", { phone, password });

  // save tokens — matches your interceptor's expected shape
  localStorage.setItem("tokens", JSON.stringify({
    access_token: data.access_token,
    refresh_token: data.refresh_token,
  }));

  // optionally save user info
  localStorage.setItem("user", JSON.stringify(data.user));

  return data;
}

export function logoutUser() {
  localStorage.removeItem("tokens");
  localStorage.removeItem("user");
  window.location.href = "/login";
}