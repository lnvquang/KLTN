"use client";

import { UserProvider } from "@/app/context/UserContext";

export default function Providers({ children }) {
    return <UserProvider>{children}</UserProvider>;
}
