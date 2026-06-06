"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { BarChart3, ClipboardList, Users, ShieldCheck } from "lucide-react";

export default function AdminSidebar() {
    const pathname = usePathname();

    const menuItems = [
        {
            name: "Thống kê",
            path: "/admin/statistics",
            icon: BarChart3,
        },
        {
            name: "Quản lý user",
            path: "/admin/users",
            icon: Users,
        },
        {
            name: "Lịch sử đánh giá",
            path: "/admin/reviews",
            icon: ClipboardList,
        },
    ];

    return (
        <aside className="sticky top-0 flex h-screen w-64 flex-col border-r border-zinc-800/60 bg-black/95 px-4 py-6 backdrop-blur-xl">
            {/* Admin Branding */}
            <div className="mb-8 flex items-center gap-3 px-2 select-none">
                <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-emerald-500/10 text-emerald-500 shadow-sm">
                    <ShieldCheck size={18} />
                </div>
                <div className="flex flex-col">
                    <span className="text-base font-bold tracking-tight text-slate-100">BigFive AI</span>
                    <span className="text-[11px] font-semibold uppercase tracking-wider text-emerald-500/80">
                        Admin Console
                    </span>
                </div>
            </div>

            {/* Navigation Section */}
            <div className="flex flex-1 flex-col">
                <div className="mb-3 px-2 text-xs font-semibold uppercase tracking-wider text-slate-500">
                    Menu Quản Trị
                </div>
                
                <nav className="flex flex-col gap-1.5">
                    {menuItems.map((item) => {
                        const Icon = item.icon;
                        const isActive = pathname === item.path || pathname?.startsWith?.(`${item.path}/`);

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
                                {/* Active Indicator mang màu cờ sắc áo của Admin (Emerald) */}
                                {isActive && (
                                    <div className="absolute left-0 top-1/2 h-1/2 w-1 -translate-y-1/2 rounded-r-full bg-emerald-500" />
                                )}
                                
                                <Icon 
                                    size={18} 
                                    className={`transition-colors duration-200 ${
                                        isActive 
                                            ? "text-emerald-400" 
                                            : "text-slate-500 group-hover:text-slate-300"
                                    }`} 
                                />
                                <span>{item.name}</span>
                            </Link>
                        );
                    })}
                </nav>
            </div>
        </aside>
    );
}