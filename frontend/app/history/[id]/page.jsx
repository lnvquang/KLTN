"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";

import Navbar from "@/components/layouts/Navbar";
import Sidebar from "@/components/layouts/Sidebar";
import { Button } from "@/components/ui/button";
import { getDetailReview } from "@/app/service/api/reviewApi";

export default function HistoryDetailPage() {
    const params = useParams();
    const idParam = params?.id;
    const reviewId = Array.isArray(idParam) ? idParam[0] : idParam;

    const [detail, setDetail] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState("");

    const traitMeta = useMemo(
        () => [
            { key: "openness", label: "Openness" },
            { key: "conscientiousness", label: "Conscientiousness" },
            { key: "extraversion", label: "Extraversion" },
            { key: "agreeableness", label: "Agreeableness" },
            { key: "neuroticism", label: "Neuroticism" },
        ],
        []
    );

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

        async function loadDetail() {
            setLoading(true);
            setError("");

            if (!reviewId) {
                setError("Thiếu id review");
                setDetail(null);
                setLoading(false);
                return;
            }

            try {
                const data = await getDetailReview(reviewId);
                if (cancelled) return;
                setDetail(data || null);
            } catch (err) {
                if (cancelled) return;
                const message = err?.response?.data?.message || err?.message || "Lỗi không xác định";
                setError(message);
                setDetail(null);
            } finally {
                if (!cancelled) setLoading(false);
            }
        }

        loadDetail();
        return () => {
            cancelled = true;
        };
    }, [reviewId]);

    const sentiment = {
        negative: normalize01(detail?.sentimentNegative),
        neutral: normalize01(detail?.sentimentNeutral),
        positive: normalize01(detail?.sentimentPositive),
    };

    const helpfulness = {
        keyAspects: normalize01(detail?.helpfulnessKeyAspects),
        advice: normalize01(detail?.helpfulnessAdvice),
        total: normalize01(detail?.helpfulnessTotal),
    };

    const preprocessedText = detail?.preprocessed_text ?? detail?.preprocessedText;
    const clusterLabel = detail?.clusterLabel ?? detail?.cluster_label;
    const clusterId = detail?.clusterId ?? detail?.cluster;

    return (
        <div className="flex">
            <Sidebar />

            <div className="flex-1">
                <Navbar />

                <main className="p-8">
                    <div className="flex items-center justify-between gap-4">
                        <div>
                            <div className="flex items-center gap-3">
                                <h1 className="text-2xl font-semibold text-slate-100">Chi tiết review</h1>
                                <span className="rounded-full border border-slate-700 bg-slate-900 px-3 py-1 text-sm text-slate-300">
                                    #{reviewId}
                                </span>
                            </div>
                            <div className="mt-2 text-sm text-slate-400">
                                {loading ? "Đang tải..." : `Tạo lúc: ${formatDateTime(detail?.createdAt)}`}
                            </div>
                        </div>

                        <Link href="/history">
                            <Button variant="outline">Quay lại</Button>
                        </Link>
                    </div>

                    {error ? (
                        <div className="mt-4 rounded-md border border-red-500 bg-red-500/10 px-4 py-3 text-sm text-red-200">
                            {error}
                        </div>
                    ) : null}

                    {!loading && !error && !detail ? (
                        <div className="mt-4 rounded-lg border border-slate-700 bg-slate-950 p-6 text-slate-400">
                            Không tìm thấy dữ liệu.
                        </div>
                    ) : null}

                    {detail ? (
                        <div className="mt-6 grid gap-4 lg:grid-cols-3">
                            <div className="lg:col-span-2 rounded-xl border border-slate-700 bg-slate-950 p-5">
                                <div className="text-sm font-semibold text-slate-200">Nội dung review</div>
                                <div className="mt-3 whitespace-pre-wrap text-slate-100">{detail.reviewText}</div>

                                {preprocessedText ? (
                                    <div className="mt-4 rounded-lg border border-slate-800 bg-slate-900/40 p-4">
                                        <div className="flex flex-wrap items-center justify-between gap-2">
                                            <div className="text-sm font-semibold text-slate-200">Text sau tiền xử lý</div>
                                            <div className="text-xs text-slate-400">
                                                Cụm: {clusterLabel || (clusterId != null ? `Cụm ${clusterId}` : "-")}
                                            </div>
                                        </div>
                                        <div className="mt-2 whitespace-pre-wrap text-sm text-slate-300">{preprocessedText}</div>
                                    </div>
                                ) : null}
                            </div>

                            <div className="rounded-xl border border-slate-700 bg-slate-950 p-5">
                                <div className="text-sm font-semibold text-slate-200">Helpfulness</div>
                                <div className="mt-3 grid gap-3">
                                    {[
                                        {
                                            key: "total",
                                            label: "Total",
                                            value: helpfulness.total,
                                            bar: "bg-emerald-500",
                                        },
                                        {
                                            key: "keyAspects",
                                            label: "Key aspects",
                                            value: helpfulness.keyAspects,
                                            bar: "bg-blue-500",
                                        },
                                        {
                                            key: "advice",
                                            label: "Advice",
                                            value: helpfulness.advice,
                                            bar: "bg-indigo-500",
                                        },
                                    ].map((row) => (
                                        <div key={row.key} className="grid gap-2">
                                            <div className="flex items-center justify-between text-xs">
                                                <span className="text-slate-300">{row.label}</span>
                                                <span className="text-slate-200">{Math.round(row.value * 100)}%</span>
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

                            <div className="rounded-xl border border-slate-700 bg-slate-950 p-5">
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
                                            key: "neutral",
                                            label: "Neutral",
                                            value: sentiment.neutral,
                                            bar: "bg-yellow-500",
                                            text: "text-yellow-200",
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
                                                <span className={row.text}>{Math.round(row.value * 100)}%</span>
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

                            <div className="lg:col-span-2 rounded-xl border border-slate-700 bg-slate-950 p-5">
                                <div className="text-sm font-semibold text-slate-200">Big Five</div>
                                <div className="mt-3 grid gap-3 sm:grid-cols-2">
                                    {traitMeta.map((t) => {
                                        const value = normalize01(detail?.[t.key]);
                                        return (
                                            <div key={t.key} className="grid gap-2">
                                                <div className="flex items-center justify-between text-xs">
                                                    <span className="text-slate-300">{t.label}</span>
                                                    <span className="text-slate-200">{Math.round(value * 100)}%</span>
                                                </div>
                                                <div className="h-2 w-full rounded-full bg-slate-800">
                                                    <div
                                                        className="h-2 rounded-full bg-blue-500"
                                                        style={{ width: `${Math.round(value * 100)}%` }}
                                                    />
                                                </div>
                                            </div>
                                        );
                                    })}
                                </div>
                            </div>
                        </div>
                    ) : null}
                </main>
            </div>
        </div>
    );
}
