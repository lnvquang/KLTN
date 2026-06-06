import api from "../api";
export const register = async (data) => {
  const response = await api.post("/auth/register", data);

  return response.data.result;
};
export const login = async (data) => {
  const response = await api.post("/auth/login", data);

  return response.data.result;
};
export const refresh = () => {
  return api.post("/auth/refresh", null, { withCredentials: true });
};
export const handleLogout = (config = {}) =>
  api.put("/auth/logout", null, { withCredentials: true, ...config });
