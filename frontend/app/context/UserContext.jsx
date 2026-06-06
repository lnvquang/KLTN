"use client";

import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";
import { usePathname, useRouter } from "next/navigation";

import { getCurrentUser } from "@/app/service/api/user";
import { sessionStore } from "@/app/service/sessionStore";

const UserContext = createContext(null);

export function UserProvider({ children }) {
    const router = useRouter();
    const pathname = usePathname();

    const [user, setUser] = useState(null);
    const [loading, setLoading] = useState(false);

    const refreshUser = useCallback(async () => {
        const token = sessionStore.getAccessToken?.();
        if (!token) {
            setUser(null);
            return null;
        }

        setLoading(true);
        try {
            const current = await getCurrentUser();
            setUser(current || null);
            return current || null;
        } finally {
            setLoading(false);
        }
    }, []);

    const clearUser = useCallback(() => {
        setUser(null);
    }, []);

    useEffect(() => {
        // Persist session across refreshes (client-only)
        refreshUser().catch(() => {
            // ignore: caller can handle on demand
        });
    }, [refreshUser]);

    useEffect(() => {
        // Global auth guard: any page except /authen requires a token
        if (pathname === "/authen") return;

        const token = sessionStore.getAccessToken?.();
        if (!token) {
            setUser(null);
            router.replace("/authen");
        }
    }, [pathname, router]);

    const value = useMemo(
        () => ({
            user,
            setUser,
            loading,
            refreshUser,
            clearUser,
        }),
        [user, loading, refreshUser, clearUser]
    );

    return <UserContext.Provider value={value}>{children}</UserContext.Provider>;
}

export function useUser() {
    const ctx = useContext(UserContext);
    if (!ctx) {
        throw new Error("useUser must be used within <UserProvider />");
    }
    return ctx;
}
