"use client";

import { useEffect, useMemo, useState } from "react";

import SentimentChart from "@/charts/SentimentChart";
import BigFiveAverageBarChart from "@/charts/BigFiveAverageBarChart";
import ReviewCountByDayChart from "@/charts/ReviewCountByDayChart";

import {
    getBigFive,
    getDashboard,
    getReviewsByDate,
    getSentiment,
} from "@/app/service/api/admin";

function StatCard({ label, value, helper }) {
    return (
        <div className="rounded-xl border border-slate-700 bg-slate-950 p-5">
            <div className="text-sm uppercase tracking-[0.18em] text-slate-500">
                {label}
            </div>
            <div className="mt-2 text-3xl font-semibold text-slate-100">{value}</div>
            {helper ? <div className="mt-2 text-sm text-slate-400">{helper}</div> : null}
        </div>
    );
}

export default function AdminStatisticsPage() {
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState("");

    const [dashboard, setDashboard] = useState(null);
    const [sentiment, setSentiment] = useState(null);
    const [bigFive, setBigFive] = useState(null);
    const [reviewsByDate, setReviewsByDate] = useState([]);

    useEffect(() => {
        let cancelled = false;

        async function load() {
            setLoading(true);
            setError("");

            try {
                const [dashboardRes, sentimentRes, bigFiveRes, reviewsByDateRes] =
                    await Promise.all([
                        getDashboard(),
                        getSentiment(),
                        getBigFive(),
                        getReviewsByDate(),
                    ]);

                if (cancelled) return;

                setDashboard(dashboardRes || null);
                setSentiment(sentimentRes || null);
                setBigFive(bigFiveRes || null);

                const list = Array.isArray(reviewsByDateRes)
                    ? reviewsByDateRes
                    : Array.isArray(reviewsByDateRes?.content)
                      ? reviewsByDateRes.content
                      : [];
                setReviewsByDate(list);
            } catch (err) {
                if (cancelled) return;
                const message = err?.response?.data?.message || err?.message || "Lỗi không xác định";
                setError(message);
                setDashboard(null);
                setSentiment(null);
                setBigFive(null);
                setReviewsByDate([]);
            } finally {
                if (!cancelled) setLoading(false);
            }
        }

        load();
        return () => {
            cancelled = true;
        };
    }, []);

    const stats = {
        totalUsers: dashboard?.totalUsers ?? 0,
        totalReviews: dashboard?.totalReviews ?? 0,
        positiveReviews: dashboard?.positiveReviews ?? 0,
        neutralReviews: dashboard?.neutralReviews ?? 0,
        negativeReviews: dashboard?.negativeReviews ?? 0,
    };

    const sentimentComputed = useMemo(() => {
        const positive = Number(sentiment?.positive ?? 0) || 0;
        const neutral = Number(sentiment?.neutral ?? 0) || 0;
        const negative = Number(sentiment?.negative ?? 0) || 0;

        const isCountLike = Math.max(positive, neutral, negative) > 1;
        const total = positive + neutral + negative;

        if (isCountLike) {
            return {
                total,
                ratio: {
                    positive: total ? positive / total : 0,
                    neutral: total ? neutral / total : 0,
                    negative: total ? negative / total : 0,
                },
            };
        }

        // Assume already normalized 0..1
        const normalizedTotal = positive + neutral + negative;
        return {
            total: stats.totalReviews || normalizedTotal,
            ratio: {
                positive,
                neutral,
                negative,
            },
        };
    }, [sentiment, stats.totalReviews]);

    const bigFiveNormalized = useMemo(() => {
        const openness = Number(bigFive?.openness ?? 0) || 0;
        const conscientiousness = Number(bigFive?.conscientiousness ?? 0) || 0;
        const extraversion = Number(bigFive?.extraversion ?? 0) || 0;
        const agreeableness = Number(bigFive?.agreeableness ?? 0) || 0;
        const neuroticism = Number(bigFive?.neuroticism ?? 0) || 0;

        const max = Math.max(openness, conscientiousness, extraversion, agreeableness, neuroticism);
        if (max <= 1) {
            return { openness, conscientiousness, extraversion, agreeableness, neuroticism };
        }
        return {
            openness: max ? openness / max : 0,
            conscientiousness: max ? conscientiousness / max : 0,
            extraversion: max ? extraversion / max : 0,
            agreeableness: max ? agreeableness / max : 0,
            neuroticism: max ? neuroticism / max : 0,
        };
    }, [bigFive]);

    return (
        <div className="space-y-6">
            <div>
                <h2 className="text-2xl font-semibold text-slate-100">Thống kê</h2>
                <p className="mt-1 text-sm text-slate-400">
                    Dữ liệu từ API admin.
                </p>
            </div>

            {error ? (
                <div className="rounded-lg border border-red-500 bg-red-500/10 px-4 py-3 text-sm text-red-200">
                    {error}
                </div>
            ) : null}

            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-5">
                <StatCard label="Total users" value={stats.totalUsers} />
                <StatCard label="Total reviews" value={stats.totalReviews} />
                <StatCard label="Positive" value={stats.positiveReviews} />
                <StatCard label="Neutral" value={stats.neutralReviews} />
                <StatCard label="Negative" value={stats.negativeReviews} />
            </div>

            <div className="grid gap-4 lg:grid-cols-2">
                <div className="rounded-xl border border-slate-700 bg-slate-950 p-5">
                    <div className="mb-4 flex items-center justify-between gap-4">
                        <h3 className="text-lg font-semibold text-slate-100">Biểu đồ Sentiment</h3>
                        <div className="text-sm text-slate-400">
                            {loading ? "Đang tải..." : `${sentimentComputed.total || 0} reviews`}
                        </div>
                    </div>
                    <SentimentChart sentiment={sentimentComputed.ratio} />
                </div>

                <div className="rounded-xl border border-slate-700 bg-slate-950 p-5">
                    <div className="mb-4 flex items-center justify-between gap-4">
                        <h3 className="text-lg font-semibold text-slate-100">Biểu đồ Big Five</h3>
                        <div className="text-sm text-slate-400">Big Five Average</div>
                    </div>

                    <BigFiveAverageBarChart values={bigFiveNormalized} />
                </div>
            </div>

            <ReviewCountByDayChart items={reviewsByDate} />
        </div>
    );
}
