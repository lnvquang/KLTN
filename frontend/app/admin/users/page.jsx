"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { Search, X, Users, Loader2, ArrowRight } from "lucide-react";

import { Button } from "@/components/ui/button";
import { getUserList, lockCustomer, unlockCustomer } from "@/app/service/api/admin";

export default function AdminUsersPage() {
    const size = 10;
    const [page, setPage] = useState(0);
    const [keyword, setKeyword] = useState("");
    const [appliedKeyword, setAppliedKeyword] = useState("");
    const [mutatingId, setMutatingId] = useState(null);

    const [usersPage, setUsersPage] = useState({
        content: [],
        page: 0,
        size,
        totalElements: 0,
        totalPages: 1,
        last: true,
    });
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState("");

    useEffect(() => {
        let cancelled = false;

        async function load() {
            setLoading(true);
            setError("");

            try {
                const result = await getUserList({
                    page,
                    size,
                    keyword: appliedKeyword,
                });
                if (cancelled) return;

                setUsersPage({
                    content: Array.isArray(result?.content) ? result.content : [],
                    page: typeof result?.page === "number" ? result.page : page,
                    size: typeof result?.size === "number" ? result.size : size,
                    totalElements: typeof result?.totalElements === "number" ? result.totalElements : 0,
                    totalPages: typeof result?.totalPages === "number" ? result.totalPages : 1,
                    last: !!result?.last,
                });
            } catch (err) {
                if (cancelled) return;
                const message = err?.response?.data?.message || err?.message || "Lỗi không xác định";
                setError(message);
                setUsersPage((prev) => ({
                    ...prev,
                    content: [],
                    totalElements: 0,
                    totalPages: 1,
                    last: true,
                }));
            } finally {
                if (!cancelled) setLoading(false);
            }
        }

        load();
        return () => {
            cancelled = true;
        };
    }, [page, size, appliedKeyword]);

    const users = usersPage.content;
    const startIndex = users.length === 0 ? 0 : usersPage.page * usersPage.size + 1;
    const endIndex = Math.min(usersPage.totalElements, usersPage.page * usersPage.size + users.length);

    function getPageItems(currentPage, totalPages, maxButtons = 5) {
        const safeTotal = Math.max(1, totalPages);
        const safeCurrent = Math.max(0, Math.min(currentPage, safeTotal - 1));
        const max = Math.max(3, maxButtons);
        
        if (safeTotal <= max) {
            return Array.from({ length: safeTotal }, (_, i) => ({ type: "page", page: i }));
        }

        const items = [];
        const windowSize = max - 2; 
        let start = Math.max(1, safeCurrent - Math.floor(windowSize / 2));
        let end = start + windowSize - 1;
        if (end > safeTotal - 2) {
            end = safeTotal - 2;
            start = end - windowSize + 1;
        }

        items.push({ type: "page", page: 0 });
        if (start > 1) items.push({ type: "ellipsis" });
        for (let p = start; p <= end; p += 1) items.push({ type: "page", page: p });
        if (end < safeTotal - 2) items.push({ type: "ellipsis" });
        items.push({ type: "page", page: safeTotal - 1 });
        
        return items;
    }

    function isActiveUser(row) {
        if (!row) return true;
        if (typeof row.status === "boolean") return row.status;
        return true;
    }

    async function toggleLock(row) {
        if (!row?.id) return;

        setMutatingId(row.id);
        setError("");
        try {
            if (isActiveUser(row)) {
                await lockCustomer(row.id);
            } else {
                await unlockCustomer(row.id);
            }

            const result = await getUserList({
                page,
                size,
                keyword: appliedKeyword,
            });

            setUsersPage({
                content: Array.isArray(result?.content) ? result.content : [],
                page: typeof result?.page === "number" ? result.page : page,
                size: typeof result?.size === "number" ? result.size : size,
                totalElements: typeof result?.totalElements === "number" ? result.totalElements : 0,
                totalPages: typeof result?.totalPages === "number" ? result.totalPages : 1,
                last: !!result?.last,
            });
        } catch (err) {
            const message = err?.response?.data?.message || err?.message || "Lỗi không xác định";
            setError(message);
        } finally {
            setMutatingId(null);
        }
    }

    function formatDate(isoString) {
        const date = new Date(isoString);
        if (Number.isNaN(date.getTime())) return "-";
        return new Intl.DateTimeFormat("vi-VN", {
            hour: "2-digit",
            minute: "2-digit",
            day: "2-digit",
            month: "2-digit",
            year: "numeric",
        }).format(date);
    }

    const handleSearch = () => {
        setPage(0);
        setAppliedKeyword(keyword.trim());
    };

    const handleClearSearch = () => {
        setKeyword("");
        setAppliedKeyword("");
        setPage(0);
    };

    return (
        <div className="space-y-6">
            {/* Header */}
            <div className="flex items-center gap-3">
                <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-emerald-500/10 text-emerald-500">
                    <Users size={20} />
                </div>
                <div>
                    <h2 className="text-xl font-bold tracking-tight text-slate-100">Quản lý User</h2>
                    <p className="text-sm text-slate-400">Xem và quản lý danh sách người dùng hệ thống.</p>
                </div>
            </div>

            {/* Toolbar: Search & Stats */}
            <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
                <div className="flex w-full max-w-md items-center gap-2 relative">
                    <div className="relative flex-1">
                        <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-500" />
                        <input
                            value={keyword}
                            onChange={(e) => setKeyword(e.target.value)}
                            onKeyDown={(e) => {
                                if (e.key === "Enter") handleSearch();
                            }}
                            placeholder="Tìm kiếm theo email, tên..."
                            className="w-full rounded-lg border border-zinc-800 bg-zinc-950/50 py-2 pl-9 pr-10 text-sm text-slate-100 placeholder:text-slate-500 outline-none transition-all focus:border-zinc-600 focus:ring-1 focus:ring-zinc-600"
                        />
                        {keyword && (
                            <button
                                onClick={handleClearSearch}
                                className="absolute right-2 top-1/2 -translate-y-1/2 rounded-full p-1 text-slate-500 hover:bg-zinc-800 hover:text-slate-300"
                            >
                                <X size={14} />
                            </button>
                        )}
                    </div>
                    <Button variant="secondary" size="sm" onClick={handleSearch}>
                        Tìm kiếm
                    </Button>
                </div>

                <div className="flex items-center gap-2 text-sm text-slate-400">
                    {loading && <Loader2 size={14} className="animate-spin text-emerald-500" />}
                    <span>{loading ? "Đang tải dữ liệu..." : `Tổng cộng ${usersPage.totalElements} tài khoản`}</span>
                </div>
            </div>

            {/* Error Message */}
            {error && (
                <div className="rounded-lg border border-red-500/50 bg-red-500/10 px-4 py-3 text-sm text-red-400">
                    {error}
                </div>
            )}

            {/* Data Table */}
            <section className="flex flex-col overflow-hidden rounded-xl border border-zinc-800/80 bg-zinc-950/50 shadow-sm">
                <div className="overflow-x-auto">
                    <table className="w-full text-left text-sm whitespace-nowrap">
                        <thead className="bg-zinc-900/50 text-xs uppercase tracking-wider text-slate-400">
                            <tr className="border-b border-zinc-800/80">
                                <th className="px-5 py-4 font-medium">#ID</th>
                                <th className="px-5 py-4 font-medium">Khách hàng</th>
                                <th className="px-5 py-4 font-medium">Số điện thoại</th>
                                <th className="px-5 py-4 font-medium">Trạng thái</th>
                                <th className="px-5 py-4 font-medium">Ngày tạo</th>
                                <th className="px-5 py-4 font-medium text-right">Thao tác</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-zinc-800/80">
                            {users.length === 0 && !loading ? (
                                <tr>
                                    <td colSpan={6} className="py-10 text-center text-slate-500">
                                        Không tìm thấy dữ liệu người dùng.
                                    </td>
                                </tr>
                            ) : (
                                users.map((u) => {
                                    const isEnabled = isActiveUser(u);
                                    const isMutating = mutatingId === u.id;
                                    
                                    return (
                                        <tr key={u.id} className="transition-colors hover:bg-zinc-900/40">
                                            <td className="px-5 py-3 font-medium text-slate-400">{u.id}</td>
                                            <td className="px-5 py-3">
                                                <div className="font-medium text-slate-200">
                                                    {[u.firstName, u.lastName].filter(Boolean).join(" ") || "Chưa cập nhật"}
                                                </div>
                                                <div className="text-xs text-slate-500">{u.email}</div>
                                            </td>
                                            <td className="px-5 py-3 text-slate-300">{u.phone || "-"}</td>
                                            <td className="px-5 py-3">
                                                {/* Đã map trạng thái vào UI */}
                                                <span className={`inline-flex items-center rounded-full px-2 py-0.5 text-[11px] font-medium ${
                                                    isEnabled 
                                                        ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20" 
                                                        : "bg-zinc-800 text-zinc-400 border border-zinc-700"
                                                }`}>
                                                    {isEnabled ? "Hoạt động" : "Đã khóa"}
                                                </span>
                                            </td>
                                            <td className="px-5 py-3 text-slate-400">
                                                {formatDate(u.createdAt)}
                                            </td>
                                            <td className="px-5 py-3 text-right">
                                                <Button
                                                    variant={isEnabled ? "destructive" : "secondary"}
                                                    size="sm"
                                                    className="h-8 mr-2"
                                                    disabled={isMutating}
                                                    onClick={() => toggleLock(u)}
                                                >
                                                    {isEnabled ? "Khóa" : "Mở khóa"}
                                                </Button>
                                                <Link href={`/admin/users/${u.id}`}>
                                                    <Button variant="ghost" size="sm" className="h-8 gap-1 text-slate-400 hover:text-slate-100">
                                                        Chi tiết <ArrowRight size={14} />
                                                    </Button>
                                                </Link>
                                            </td>
                                        </tr>
                                    );
                                })
                            )}
                        </tbody>
                    </table>
                </div>

                {/* Pagination */}
                <div className="flex flex-col gap-4 border-t border-zinc-800/80 bg-zinc-900/20 px-5 py-4 sm:flex-row sm:items-center sm:justify-between">
                    <div className="text-xs text-slate-400">
                        Hiển thị <span className="font-medium text-slate-200">{startIndex}</span> đến <span className="font-medium text-slate-200">{endIndex}</span> trong số <span className="font-medium text-slate-200">{usersPage.totalElements}</span>
                    </div>

                    <div className="flex items-center gap-1.5">
                        <Button
                            variant="outline"
                            size="sm"
                            className="h-8 border-zinc-700 bg-transparent text-xs text-slate-300 hover:bg-zinc-800 hover:text-slate-100"
                            disabled={usersPage.page <= 0}
                            onClick={() => setPage((p) => Math.max(0, p - 1))}
                        >
                            Trước
                        </Button>

                        <div className="flex items-center gap-1 px-2">
                            {getPageItems(usersPage.page, usersPage.totalPages, 5).map((item, idx) => {
                                if (item.type === "ellipsis") {
                                    return <span key={`ellipsis-${idx}`} className="px-1 text-xs text-slate-500">...</span>;
                                }
                                const isActive = item.page === usersPage.page;
                                return (
                                    <button
                                        key={`page-${item.page}`}
                                        onClick={() => setPage(item.page)}
                                        className={`flex h-7 w-7 items-center justify-center rounded-md text-xs font-medium transition-colors ${
                                            isActive 
                                                ? "bg-zinc-700 text-slate-100" 
                                                : "text-slate-400 hover:bg-zinc-800 hover:text-slate-200"
                                        }`}
                                    >
                                        {item.page + 1}
                                    </button>
                                );
                            })}
                        </div>

                        <Button
                            variant="outline"
                            size="sm"
                            className="h-8 border-zinc-700 bg-transparent text-xs text-slate-300 hover:bg-zinc-800 hover:text-slate-100"
                            disabled={usersPage.last}
                            onClick={() => setPage((p) => Math.min(usersPage.totalPages - 1, p + 1))}
                        >
                            Sau
                        </Button>
                    </div>
                </div>
            </section>
        </div>
    );
}