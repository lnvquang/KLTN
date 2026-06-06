"use client";

import { useEffect, useMemo, useRef, useState, useCallback } from "react";
import { useRouter } from "next/navigation";
import { ChevronDown, LogOut, Sparkles } from "lucide-react";

import { useUser } from "@/app/context/UserContext";
import { handleLogout } from "@/app/service/api/authen";
import { sessionStore } from "@/app/service/sessionStore";
import { Button } from "@/components/ui/button";


export default function Navbar() {
    const router = useRouter();
    const { user, clearUser } = useUser();
    const fullName = [user?.firstName, user?.lastName].filter(Boolean).join(" ");

    // Thêm state để kiểm tra component đã mount trên client chưa
    const [isMounted, setIsMounted] = useState(false);
    const [open, setOpen] = useState(false);
    const menuRef = useRef(null);

    const initials = useMemo(() => {
        const first = (user?.firstName || "").trim();
        const last = (user?.lastName || "").trim();
        const a = first ? first[0] : "";
        const b = last ? last[0] : "";
        return `${a}${b}`.toUpperCase() || "U";
    }, [user?.firstName, user?.lastName]);

    const hasToken = !!sessionStore.getAccessToken?.();

    const onLogout = async () => {
        try {
            await handleLogout();
        } catch(error) {
           console.log(error);
           
        } finally {
            sessionStore.clearAccessToken();
            clearUser?.();
            router.replace("/authen");
        }
    };

    const handleClickOutside = useCallback((e) => {
        if (menuRef.current && !menuRef.current.contains(e.target)) {
            setOpen(false);
        }
    }, []);

    // Effect 1: Đánh dấu component đã mount xong trên client
    useEffect(() => {
        setIsMounted(true);
    }, []);

    // Effect 2: Xử lý click outside
    useEffect(() => {
        if (!open) return;
        document.addEventListener("mousedown", handleClickOutside);
        document.addEventListener("touchstart", handleClickOutside);
        return () => {
            document.removeEventListener("mousedown", handleClickOutside);
            document.removeEventListener("touchstart", handleClickOutside);
        };
    }, [open, handleClickOutside]);

    return (
        <nav className="sticky top-0 z-50 flex h-16 w-full items-center justify-between border-b border-zinc-800/60 bg-black/80 px-6 backdrop-blur-md">
            {/* Logo Section */}
            <div className="flex items-center gap-3 select-none">
                <div className="flex items-center justify-center rounded-lg bg-zinc-800 p-1.5 text-slate-100">
                    <Sparkles size={18} />
                </div>
                <div className="flex items-baseline gap-2">
                    <h1 className="text-xl font-bold tracking-tight text-slate-100">BigFive AI</h1>
                    <span className="rounded-full bg-zinc-800/50 px-2 py-0.5 text-xs font-medium text-slate-400">
                        Dashboard
                    </span>
                </div>
            </div>

            {/* User Section - Chỉ render khi đã mounted trên client */}
            {isMounted && hasToken && (
                <div className="relative" ref={menuRef}>
                    <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => setOpen((v) => !v)}
                        aria-expanded={open}
                        className="group flex h-10 items-center gap-3 rounded-full border border-transparent px-2 hover:bg-zinc-900 hover:border-zinc-800 transition-all"
                    >
                        <span className="flex h-7 w-7 items-center justify-center rounded-full bg-zinc-800 text-xs font-semibold text-slate-200 group-hover:bg-zinc-700 transition-colors">
                            {initials}
                        </span>
                        <span className="hidden text-sm font-medium text-slate-200 sm:block">
                            {fullName || "Tài khoản"}
                        </span>
                        <ChevronDown 
                            size={16} 
                            className={`text-slate-400 transition-transform duration-200 ${open ? "rotate-180" : ""}`} 
                        />
                    </Button>

                    {/* Dropdown Menu */}
                    <div
                        className={`absolute right-0 mt-2 w-52 origin-top-right rounded-xl border border-zinc-800 bg-zinc-950 p-1.5 shadow-2xl transition-all duration-200 ease-out ${
                            open
                                ? "scale-100 opacity-100 pointer-events-auto translate-y-0"
                                : "scale-95 opacity-0 pointer-events-none -translate-y-2"
                        }`}
                    >
                        <div className="px-2 py-2.5 sm:hidden">
                            <p className="text-sm font-medium text-slate-200 truncate">
                                {fullName || "Tài khoản"}
                            </p>
                        </div>
                        <div className="h-px bg-zinc-800 my-1 sm:hidden" />
                        
                        <button
                            type="button"
                            onClick={async () => {
                                setOpen(false);
                                await onLogout();
                            }}
                            className="flex w-full items-center gap-3 rounded-md px-2.5 py-2 text-sm font-medium text-slate-300 transition-colors hover:bg-red-500/10 hover:text-red-400 focus:bg-red-500/10 focus:text-red-400 focus:outline-none"
                        >
                            <LogOut size={16} />
                            Đăng xuất
                        </button>
                    </div>
                </div>
            )}
        </nav>
    );
}