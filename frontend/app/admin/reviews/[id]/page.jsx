"use client";

import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { useEffect, useMemo, useState } from "react";

import { Button } from "@/components/ui/button";
import { getReviewDetail } from "@/app/service/api/admin";

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

function normalize01(value) {
    if (typeof value !== "number" || Number.isNaN(value)) return 0;
    if (value <= 1) return Math.max(0, Math.min(1, value));
    return Math.max(0, Math.min(1, value / 100.0));
}

export default function AdminReviewDetailPage() {
    const router = useRouter();
    const params = useParams();
    const idParam = params?.id;
    const reviewId = useMemo(() => {
        const raw = Array.isArray(idParam) ? idParam[0] : idParam;
        const n = Number(raw);
        return Number.isFinite(n) ? n : null;
    }, [idParam]);

    const [loading, setLoading] = useState(true);
    const [error, setError] = useState("");
    const [review, setReview] = useState(null);

    useEffect(() => {
        let cancelled = false;

        async function load() {
            if (reviewId == null) {
                setLoading(false);
                setError("Review id không hợp lệ");
                setReview(null);
                return;
            }

            setLoading(true);
            setError("");
            try {
                const detail = await getReviewDetail(reviewId);
                if (cancelled) return;
                setReview(detail || null);
            } catch (err) {
                if (cancelled) return;
                const message = err?.response?.data?.message || err?.message || "Lỗi không xác định";
                setError(message);
                setReview(null);
            } finally {
                if (!cancelled) setLoading(false);
            }
        }

        load();
        return () => {
            cancelled = true;
        };
    }, [reviewId]);

    const positive = normalize01(review?.sentimentPositive);
    const negative = normalize01(review?.sentimentNegative);
    const neutral = normalize01(review?.sentimentNeutral);

    const clusterLabel = review?.clusterLabel ?? review?.cluster_label;
    const clusterId = review?.clusterId ?? review?.cluster;
    const preprocessedText = review?.preprocessed_text ?? review?.preprocessedText;

    return (
        <div className="space-y-6">
            <div className="flex flex-wrap items-end justify-between gap-3">
                <div>
                    <h2 className="text-2xl font-semibold text-slate-100">Chi tiết review</h2>
                   
                </div>
                <Button variant="outline" size="sm" onClick={() => router.back()}>
                    Quay lại
                </Button>
            </div>

            {error ? (
                <div className="rounded-md border border-red-500 bg-red-500/10 px-4 py-3 text-sm text-red-200">
                    {error}
                </div>
            ) : null}

            {loading ? (
                <div className="text-sm text-slate-400">Đang tải...</div>
            ) : null}

            {!loading && !review ? (
                <div className="space-y-3">
                    <div className="text-sm text-slate-400">Không tìm thấy review.</div>
                    <Link href="/admin/users">
                        <Button variant="outline" size="sm">Về quản lý user</Button>
                    </Link>
                </div>
            ) : null}

            {review ? (
            <section className="rounded-xl border border-slate-700 bg-slate-950 p-5">
                <div className="flex flex-wrap items-center justify-between gap-3">
                    <div>
                        <div className="text-lg font-semibold text-slate-100">Review #{review.id}</div>
                        <div className="text-sm text-slate-400">
                            {formatDateTime(review.createdAt)}
                        </div>
                    </div>
                    <div className="flex flex-wrap items-center gap-2">
                        <div className="rounded-full border border-slate-700 bg-slate-900 px-3 py-1 text-sm text-slate-200">
                            Cụm: {clusterLabel || (clusterId != null ? `Cụm ${clusterId}` : "-")}
                        </div>
                        <div className="rounded-full border border-slate-700 bg-slate-900 px-3 py-1 text-sm text-slate-200">
                            Helpfulness: {Math.round(normalize01(review.helpfulnessTotal) * 100)}%
                        </div>
                    </div>
                </div>

                <div className="mt-4 whitespace-pre-wrap text-slate-100">{review.reviewText}</div>

                {preprocessedText ? (
                    <div className="mt-4 rounded-lg border border-slate-800 bg-slate-900/40 p-4">
                        <div className="text-sm font-semibold text-slate-200">Text sau tiền xử lý</div>
                        <div className="mt-2 whitespace-pre-wrap text-sm text-slate-300">{preprocessedText}</div>
                    </div>
                ) : null}

                <div className="mt-6 rounded-lg border border-slate-800 bg-slate-900/40 p-4">
                    <div className="text-sm font-semibold text-slate-200">Sentiment</div>

                    <div className="mt-3 grid gap-3">
                        {[
                            {
                                key: "negative",
                                label: "Negative",
                                value: negative,
                                bar: "bg-red-500",
                                text: "text-red-300",
                            },
                            {
                                key: "neutral",
                                label: "Neutral",
                                value: neutral,
                                bar: "bg-yellow-500",
                                text: "text-yellow-300",
                            },
                            {
                                key: "positive",
                                label: "Positive",
                                value: positive,
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
            </section>
            ) : null}
        </div>
    );
}
