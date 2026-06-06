"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { MessageSquare, Loader2, ArrowRight } from "lucide-react";

import { Button } from "@/components/ui/button";
import { getAllReviews } from "@/app/service/api/admin";

export default function AdminReviewsPage() {
    const size = 5;
    const [page, setPage] = useState(0);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState("");

    const [reviewsPage, setReviewsPage] = useState({
        content: [],
        page: 0,
        size,
        totalElements: 0,
        totalPages: 1,
        last: true,
    });

    useEffect(() => {
        let cancelled = false;

        async function load() {
            setLoading(true);
            setError("");
            try {
                const result = await getAllReviews({ page, size });
                if (cancelled) return;

                setReviewsPage({
                    content: Array.isArray(result?.content) ? result.content : [],
                    page: typeof result?.number === "number"
                        ? result.number
                        : typeof result?.page === "number"
                          ? result.page
                          : page,
                    size: typeof result?.size === "number" ? result.size : size,
                    totalElements: typeof result?.totalElements === "number" ? result.totalElements : 0,
                    totalPages: typeof result?.totalPages === "number" ? result.totalPages : 1,
                    last: !!result?.last,
                });
            } catch (err) {
                if (cancelled) return;
                const message = err?.response?.data?.message || err?.message || "Lỗi không xác định";
                setError(message);
                setReviewsPage((prev) => ({
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
    }, [page, size]);

    const reviews = reviewsPage.content;
    const startIndex = reviews.length === 0 ? 0 : reviewsPage.page * reviewsPage.size + 1;
    const endIndex = Math.min(reviewsPage.totalElements, reviewsPage.page * reviewsPage.size + reviews.length);

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

    function formatDateTime(isoString) {
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

    // Helper function để định dạng màu sắc cho cảm xúc (Sentiment)
    function getSentimentBadge(positiveValue) {
        const value = Math.round((positiveValue || 0) * 100);
        if (value >= 70) {
            return { text: `${value}% Tích cực`, color: "bg-emerald-500/10 text-emerald-400 border-emerald-500/20" };
        }
        if (value >= 40) {
            return { text: `${value}% Trung lập`, color: "bg-amber-500/10 text-amber-400 border-amber-500/20" };
        }
        return { text: `${value}% Tiêu cực`, color: "bg-red-500/10 text-red-400 border-red-500/20" };
    }

    return (
        <div className="space-y-6">
            {/* Header */}
            <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
                <div className="flex items-center gap-3">
                    <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-emerald-500/10 text-emerald-500">
                        <MessageSquare size={20} />
                    </div>
                    <div>
                        <h2 className="text-xl font-bold tracking-tight text-slate-100">Lịch sử đánh giá</h2>
                        <p className="text-sm text-slate-400">
                            Quản lý và theo dõi phản hồi từ người dùng hệ thống.
                        </p>
                    </div>
                </div>

                <div className="flex items-center gap-2 text-sm text-slate-400">
                    {loading && <Loader2 size={14} className="animate-spin text-emerald-500" />}
                    <span>{loading ? "Đang tải dữ liệu..." : `Tổng cộng ${reviewsPage.totalElements} đánh giá`}</span>
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
                                <th className="px-5 py-4 font-medium">Người đánh giá</th>
                                <th className="px-5 py-4 font-medium">Cảm xúc</th>
                                <th className="px-5 py-4 font-medium">Cụm</th>
                                <th className="px-5 py-4 font-medium">Thời gian</th>
                                <th className="px-5 py-4 font-medium w-full max-w-[300px]">Nội dung</th>
                                <th className="px-5 py-4 font-medium text-right">Thao tác</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-zinc-800/80">
                            {reviews.length === 0 && !loading ? (
                                <tr>
                                    <td colSpan={7} className="py-10 text-center text-slate-500">
                                        Không có đánh giá nào được tìm thấy.
                                    </td>
                                </tr>
                            ) : (
                                reviews.map((r) => {
                                    const sentiment = getSentimentBadge(r.sentimentPositive);
                                    const clusterLabel = r?.clusterLabel ?? r?.cluster_label;
                                    const clusterId = r?.clusterId ?? r?.cluster;
                                    return (
                                        <tr key={r.id} className="transition-colors hover:bg-zinc-900/40">
                                            <td className="px-5 py-3 font-medium text-slate-400">{r.id}</td>
                                            <td className="px-5 py-3">
                                                <div className="font-medium text-slate-200">{r.fullName || "Ẩn danh"}</div>
                                                <div className="text-xs text-slate-500">User ID: {r.userId}</div>
                                            </td>
                                            <td className="px-5 py-3">
                                                <span className={`inline-flex items-center rounded-full border px-2.5 py-0.5 text-[11px] font-semibold ${sentiment.color}`}>
                                                    {sentiment.text}
                                                </span>
                                            </td>
                                            <td className="px-5 py-3 text-slate-300">
                                                {clusterLabel || (clusterId != null ? `Cụm ${clusterId}` : "-")}
                                            </td>
                                            <td className="px-5 py-3 text-slate-400">
                                                {formatDateTime(r.createdAt)}
                                            </td>
                                            <td className="px-5 py-3">
                                                {/* Cắt chữ nếu đánh giá quá dài */}
                                                <div 
                                                    className="max-w-[200px] truncate text-slate-300 sm:max-w-[300px]" 
                                                    title={r.reviewText}
                                                >
                                                    {r.reviewText || <span className="text-slate-600 italic">Không có nội dung</span>}
                                                </div>
                                            </td>
                                            <td className="px-5 py-3 text-right">
                                                <Link href={`/admin/reviews/${r.id}`}>
                                                    <Button variant="ghost" size="sm" className="h-8 gap-1 text-slate-400 hover:text-slate-100">
                                                        Xem <ArrowRight size={14} />
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
                        Hiển thị <span className="font-medium text-slate-200">{startIndex}</span> đến <span className="font-medium text-slate-200">{endIndex}</span> trong số <span className="font-medium text-slate-200">{reviewsPage.totalElements}</span>
                    </div>

                    <div className="flex items-center gap-1.5">
                        <Button
                            variant="outline"
                            size="sm"
                            className="h-8 border-zinc-700 bg-transparent text-xs text-slate-300 hover:bg-zinc-800 hover:text-slate-100"
                            disabled={reviewsPage.page <= 0}
                            onClick={() => setPage((p) => Math.max(0, p - 1))}
                        >
                            Trước
                        </Button>

                        <div className="flex items-center gap-1 px-2">
                            {getPageItems(reviewsPage.page, reviewsPage.totalPages, 5).map((item, idx) => {
                                if (item.type === "ellipsis") {
                                    return <span key={`ellipsis-${idx}`} className="px-1 text-xs text-slate-500">...</span>;
                                }
                                const isActive = item.page === reviewsPage.page;
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
                            disabled={reviewsPage.last}
                            onClick={() => setPage((p) => Math.min(reviewsPage.totalPages - 1, p + 1))}
                        >
                            Sau
                        </Button>
                    </div>
                </div>
            </section>
        </div>
    );
}