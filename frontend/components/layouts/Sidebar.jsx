"use client";

import Link from "next/link";
import { House, History, Radar, Sparkles } from "lucide-react";
import { usePathname } from "next/navigation";

export default function Sidebar() {
    const pathname = usePathname();
    const menuItems = [
        {
            name: "Home",
            path: "/",
            icon: House,
        },
        {
            name: "Predict",
            path: "/predict",
            icon: Radar,
        },
        {
            name: "History",
            path: "/history",
            icon: History,
        }
    ];

    return (
        <aside className="sticky top-0 flex h-screen w-64 flex-col border-r border-zinc-800/60 bg-black/95 px-4 py-6 backdrop-blur-xl">
            {/* Branding Section */}
            <div className="mb-8 flex items-center gap-3 px-2 select-none">
                <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-zinc-800 text-slate-100 shadow-sm">
                    <Sparkles size={16} />
                </div>
                <div className="flex flex-col">
                    <span className="text-base font-bold tracking-tight text-slate-100">BigFive AI</span>
                    <span className="text-[11px] font-medium uppercase tracking-wider text-slate-500">
                        Customer Personality
                    </span>
                </div>
            </div>

            {/* Navigation Section */}
            <div className="flex flex-1 flex-col">
                <div className="mb-3 px-2 text-xs font-semibold uppercase tracking-wider text-slate-500">
                    Menu
                </div>
                
                <nav className="flex flex-col gap-1.5">
                    {menuItems.map((item) => {
                        const Icon = item.icon;
                        const isActive =
                            item.path === "/history"
                                ? pathname === "/history" || pathname?.startsWith?.("/history/")
                                : pathname === item.path;

                        return (
                            <Link
                                key={item.path}
                                href={item.path}
                                className={`group relative flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-all duration-200 ease-in-out ${
                                    isActive
                                        ? "bg-zinc-800/80 text-slate-100"
                                        : "text-slate-400 hover:bg-zinc-900/50 hover:text-slate-200"
                                }`}
                            >
                                {/* Active Indicator (Vạch dọc bên trái) */}
                                {isActive && (
                                    <div className="absolute left-0 top-1/2 h-1/2 w-1 -translate-y-1/2 rounded-r-full bg-slate-200" />
                                )}
                                
                                <Icon 
                                    size={18} 
                                    className={`transition-colors duration-200 ${
                                        isActive 
                                            ? "text-slate-200" 
                                            : "text-slate-500 group-hover:text-slate-300"
                                    }`} 
                                />
                                <span>{item.name}</span>
                            </Link>
                        );
                    })}
                </nav>
            </div>
            
            {/* (Tùy chọn) Khu vực Footer của Sidebar có thể đặt ở đây */}
            {/* <div className="mt-auto px-2">...</div> */}
        </aside>
    );
}