export const sessionStore = {
    setAccessToken(token) {
        if (!token) return;
        if (typeof window === "undefined") return;
        if (typeof sessionStorage === "undefined") return;

        sessionStorage.setItem("accessToken", token);
    },

    getAccessToken() {
        if (typeof window === "undefined") return null;
        if (typeof sessionStorage === "undefined") return null;

        return sessionStorage.getItem("accessToken");
    },

    clearAccessToken() {
        if (typeof window === "undefined") return;
        if (typeof sessionStorage === "undefined") return;

        sessionStorage.removeItem("accessToken");
    },
};
