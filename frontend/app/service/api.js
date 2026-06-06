import axios from "axios";

import { sessionStore } from "./sessionStore";


let refreshInFlight = null;
let accountLockedNotified = false;

function isAuthPath(url) {
    if (!url) return false;
    return url.includes("/auth/login") || url.includes("/auth/refresh") || url.includes("/auth/logout");
}

function extractAuthCode(data) {
    if (!data) return null;
    if (typeof data === "string") return null;
    return data.code || data?.result?.code || data?.error?.code || null;
}

function notifyAccountLocked(message) {
    if (accountLockedNotified) return;
    accountLockedNotified = true;

    if (typeof window === "undefined") return;
    const fallback = "Tài khoản của bạn đã bị khóa. Vui lòng liên hệ quản trị viên.";
    // alert is required by UX request
    window.alert(message || fallback);
}

async function clientLogout() {
    const token = sessionStore.getAccessToken?.();
    try {
        await axios.put(
            "http://localhost:8080/api/auth/logout",
            null,
            {
                withCredentials: true,
                headers: {
                    "Content-Type": "application/json",
                    ...(token ? { Authorization: `Bearer ${token}` } : {}),
                },
                timeout: 1000000,
            }
        );
    } catch {
        // ignore
    }

    sessionStore.clearAccessToken();

    if (typeof window !== "undefined") {
        window.location.replace("/authen");
    }
}

const api = axios.create({
    baseURL: "http://localhost:8080/api",
    withCredentials: true,
    headers: {
        "Content-Type": "application/json",
    },
    timeout: 1000000,
});

async function refreshAccessToken() {
    if (refreshInFlight) return refreshInFlight;

    refreshInFlight = api.post("/auth/refresh", null, {
        withCredentials: true,
        _skipAuthRefresh: true,
        _skipAuthLogout: true,
    });

    try {
        const response = await refreshInFlight;
        const newToken =
            response?.data?.result?.accessToken ||
            response?.data?.accessToken ||
            null;
        if (!newToken) {
            throw new Error("Refresh succeeded but no accessToken returned");
        }
        sessionStore.setAccessToken(newToken);
      
        return newToken;
    } finally {
        refreshInFlight = null;
    }
}

api.interceptors.request.use(
    (config) => {
        const url = config?.url || "";
        if (isAuthPath(url)) return config;

        const token = sessionStore.getAccessToken?.();
        if (!token) return config;

        config.headers = config.headers || {};
        if (!config._preserveAuthHeader) {
            // Always overwrite to avoid using a stale token after refresh.
            config.headers.Authorization = `Bearer ${token}`;
        }

        return config;
    },
    (error) => Promise.reject(error)
);

api.interceptors.response.use(
    (response) => response,
    async (error) => {
        

        const originalRequest = error?.config;
        const response = error?.response;

        if (!originalRequest || !response) {
            return Promise.reject(error);
        }

        const url = originalRequest.url || "";
        if (isAuthPath(url)) {
            return Promise.reject(error);
        }

        if (originalRequest._skipAuthRefresh) {
            return Promise.reject(error);
        }

        const code = extractAuthCode(response.data);

       
        if (code === "TOKEN_EXPIRED" && !originalRequest._retry) {
            originalRequest._retry = true;
            try {
                const newToken = await refreshAccessToken();
                originalRequest.headers = originalRequest.headers || {};
                originalRequest.headers.Authorization = `Bearer ${newToken}`;
                return api(originalRequest);
            } catch (refreshErr) {
                const refreshStatus = refreshErr?.response?.status;
                const refreshCode = extractAuthCode(refreshErr?.response?.data);
                const refreshMessage = refreshErr?.response?.data?.message;
                if (refreshCode === "ACCOUNT_LOCKED" || refreshStatus === 423) {
                    notifyAccountLocked(refreshMessage);
                }
                await clientLogout();
                // Interceptor is handling auth (redirect), don't surface auth errors to UI.
                return new Promise(() => {});
            }
        }

      
        if (
            code === "TOKEN_INVALID" ||
            code === "TOKEN_REVOKED" ||
            code === "ACCOUNT_LOCKED" ||
            code === "UNAUTHORIZED" ||
            response.status === 401 ||
            response.status === 423
        ) {
            if (!originalRequest._skipAuthLogout) {
                if (code === "ACCOUNT_LOCKED" || response.status === 423) {
                    notifyAccountLocked(response?.data?.message);
                }
                await clientLogout();
                // Interceptor is handling auth (redirect), don't surface auth errors to UI.
                return new Promise(() => {});
            }
        }

        return Promise.reject(error);
    }
);

export default api;