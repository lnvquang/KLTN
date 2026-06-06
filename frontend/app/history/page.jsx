"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import Navbar from "@/components/layouts/Navbar";
import Sidebar from "@/components/layouts/Sidebar";
import { getHistoryReview } from "@/app/service/api/reviewApi";
import { Button } from "@/components/ui/button";

export default function HistoryPage() {
    const [history, setHistory] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState("");

    function normalize01(value) {
        if (typeof value !== "number" || Number.isNaN(value)) return 0;
        if (value <= 1) return Math.max(0, Math.min(1, value));
        return Math.max(0, Math.min(1, value / 100.0));
    }

    function formatDateTime(isoString) {
        if (!isoString) return "-";
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

    useEffect(() => {
        let cancelled = false;

        async function loadHistory() {
            setLoading(true);
            setError("");

            try {
                const items = await getHistoryReview();
                if (cancelled) return;
                setHistory(Array.isArray(items) ? items : []);
            } catch (err) {
                if (cancelled) return;
                const message = err?.response?.data?.message || err?.message || "Lỗi không xác định";
                setError(message);
                setHistory([]);
            } finally {
                if (!cancelled) setLoading(false);
            }
        }

        loadHistory();
        return () => {
            cancelled = true;
        };
    }, []);

    return (
        <div className="flex">
            <Sidebar />

            <div className="flex-1">
                <Navbar />

                <main className="p-8">
                    <div className="flex items-center justify-between gap-4">
                        <h1 className="text-2xl font-semibold text-slate-100">Lịch sử review</h1>
                        <div className="text-sm text-slate-400">
                            {loading ? "Đang tải..." : `${history.length} bản ghi`}
                        </div>
                    </div>

                    <div className="mt-2 text-sm text-slate-400">
                        Chọn một bản ghi để xem chi tiết review.
                    </div>

                    {error ? (
                        <div className="mt-4 rounded-md border border-red-500 bg-red-500/10 px-4 py-3 text-sm text-red-200">
                            {error}
                        </div>
                    ) : null}

                    {!loading && !error && history.length === 0 ? (
                        <div className="mt-4 rounded-lg border border-slate-700 bg-slate-950 p-6 text-slate-400">
                            Chưa có lịch sử review.
                        </div>
                    ) : null}

                    <div className="mt-6 grid gap-4">
                        {history.map((item) => {
                            const reviewId = item.id;

                            const sentiment = {
                                negative: normalize01(item.sentimentNegative),
                                positive: normalize01(item.sentimentPositive),
                            };

                            const helpfulnessTotal = normalize01(item.helpfulnessTotal);

                            return (
                                <div
                                    key={reviewId ?? item.createdAt ?? item.reviewText}
                                    className="rounded-xl border border-slate-700 bg-slate-950 p-5"
                                >
                                    <div className="flex flex-col gap-5 lg:flex-row lg:items-start lg:justify-between">
                                        <div className="min-w-0 flex-1">
                                            <div className="flex flex-wrap items-center gap-x-3 gap-y-2 text-sm text-slate-400">
                                                <span className="rounded-full border border-slate-700 bg-slate-900 px-3 py-1">
                                                    Review #{reviewId}
                                                </span>
                                                <span>{formatDateTime(item.createdAt)}</span>
                                                <span className="rounded-full border border-slate-700 bg-slate-900 px-3 py-1">
                                                    Helpfulness: {Math.round(helpfulnessTotal * 100)}%
                                                </span>

                                                {reviewId != null ? (
                                                    <Link
                                                        href={`/history/${reviewId}`}
                                                        className="ml-auto w-full sm:w-auto"
                                                    >
                                                        <Button
                                                            variant="outline"
                                                            size="sm"
                                                            className="w-full sm:w-auto"
                                                        >
                                                            Xem chi tiết
                                                        </Button>
                                                    </Link>
                                                ) : null}
                                            </div>

                                            <div className="mt-4 whitespace-pre-wrap text-slate-100">
                                                {item.reviewText}
                                            </div>
                                        </div>

                                        <div className="w-full lg:w-[380px] flex-shrink-0 rounded-lg border border-slate-800 bg-slate-900/40 p-4">
                                            <div className="text-sm font-semibold text-slate-200">Sentiment</div>

                                            <div className="mt-3 grid gap-3">
                                                {[
                                                    {
                                                        key: "negative",
                                                        label: "Negative",
                                                        value: sentiment.negative,
                                                        bar: "bg-red-500",
                                                        text: "text-red-300",
                                                    },
                                                    {
                                                        key: "positive",
                                                        label: "Positive",
                                                        value: sentiment.positive,
                                                        bar: "bg-green-500",
                                                        text: "text-green-300",
                                                    },
                                                ].map((row) => (
                                                    <div key={row.key} className="grid gap-2">
                                                        <div className="flex items-center justify-between text-xs">
                                                            <span className="text-slate-300">{row.label}</span>
                                                            <span className={row.text}>
                                                                {Math.round(row.value * 100)}%
                                                            </span>
                                                        </div>
                                                        <div className="h-2 w-full rounded-full bg-slate-800">
                                                            <div
                                                                className={`h-2 rounded-full ${row.bar}`}
                                                                style={{ width: `${Math.round(row.value * 100)}%` }}
                                                            />
                                                        </div>
                                                    </div>
                                                ))}
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            );
                        })}
                    </div>
                </main>
            </div>
        </div>
    );
}
