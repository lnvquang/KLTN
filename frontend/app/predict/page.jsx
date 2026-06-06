"use client";

import { useState } from "react";
import PersonalityRadar from "@/charts/PersonalityRadar";
import SentimentChart from "@/charts/SentimentChart";
import Navbar from "@/components/layouts/Navbar";
import Sidebar from "@/components/layouts/Sidebar";
import styles from "./page.module.css";
import ClusterCard from "@/components/cards/ClusterCard";
import HelpfulnessCard from "@/components/cards/HelpfulnessCard";
import { analyzeReview } from "@/app/service/api/reviewApi";

export default function PredictPage() {
    const [text, setText] = useState("");
    const [result, setResult] = useState(null);
    const [multitaskResult, setMultitaskResult] = useState(null);
    const [analysis, setAnalysis] = useState(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState("");

    function formatScore(value) {
        if (typeof value !== "number") return "-";
        return value.toFixed(2);
    }

    function getSentimentLabel(sentimentObj) {
        if (!sentimentObj) return 1; // default neutral
        const { negative, neutral, positive } = sentimentObj;
        const max = Math.max(negative || 0, neutral || 0, positive || 0);
        if (max === positive) return 2; // positive
        if (max === negative) return 0; // negative
        return 1; // neutral
    }

    async function handlePredict() {
        if (!text.trim()) {
            setError("Vui lòng nhập nội dung trước khi dự đoán.");
            return;
        }

        setError("");
        setLoading(true);
        setResult(null);
        setMultitaskResult(null);
        setAnalysis(null);

        try {
            // Single endpoint: /api/reviews/analyze
            // Expected shape (after analyzeReview): { multitask, personality_logits, personality_probs, reviewId }
            const analyzeResult = await analyzeReview(text);

            setAnalysis(analyzeResult || null);

            const personality = analyzeResult?.personality_logits ?? analyzeResult?.personality;
            const multitask = analyzeResult?.multitask;

            // Keep raw logits when available; only pass numeric values through.
            const normalized = {};
            if (personality && typeof personality === "object") {
                Object.entries(personality).forEach(([k, v]) => {
                    if (typeof v === "number") {
                        normalized[k] = v;
                    } else {
                        normalized[k] = v;
                    }
                });
            }

            setResult(Object.keys(normalized).length ? normalized : null);
            setMultitaskResult(multitask || null);
        } catch (err) {
            const message = err?.response?.data?.message || err?.message || "Lỗi không xác định";
            setError(message);
        } finally {
            setLoading(false);
        }
    }

    const clusterLabel = analysis?.cluster_label ?? analysis?.clusterLabel;
    const clusterId = analysis?.cluster ?? analysis?.clusterId;
    const preprocessedText = analysis?.preprocessed_text ?? analysis?.preprocessedText;

    return (
        <div className="flex">
            <Sidebar />

            <div className="flex-1">
                <Navbar />

                <main className="p-8">
                    <div>
                        <div className={`shadow-xl flex flex-col ${styles.predictContainer}`}>
                            <h1>PSYCHOLOGICAL INPUT SOURCE</h1>

                            <textarea
                                value={text}
                                onChange={(event) => setText(event.target.value)}
                                className="w-full h-20 p-4 rounded-lg border border-zinc-700 bg-slate-950 text-white"
                                placeholder="Enter customer comment..."
                                maxLength={3000}
                            />

                            {preprocessedText ? (
                                <div className="mt-4 rounded-lg border border-slate-700 bg-slate-950 p-4">
                                    <div className="text-sm font-semibold text-slate-200">Text sau tiền xử lý</div>
                                    <div className="mt-2 whitespace-pre-wrap text-sm text-slate-300">
                                        {preprocessedText}
                                    </div>
                                </div>
                            ) : null}

                            <button
                                onClick={handlePredict}
                                disabled={loading}
                                className="mt-4 px-6 py-2 self-end rounded-md bg-blue-600 text-white hover:bg-blue-500 disabled:opacity-50"
                            >
                                {loading ? "Đang dự đoán..." : "Predict"}
                            </button>

                            {error ? (
                                <div className="mt-4 rounded-md border border-red-500 bg-red-500/10 px-4 py-3 text-sm text-red-200">
                                    {error}
                                </div>
                            ) : null}
                        </div>

                        <div className="mt-10 flex w-full gap-4">
                            <div className="flex-1">
                                {result ? (
                                    <>
                                        <PersonalityRadar data={result} />

                                        <div className="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
                                            {Object.entries(result).map(([trait, value]) => (
                                                <div
                                                    key={trait}
                                                    className="rounded-xl border border-slate-700 bg-slate-950 p-4"
                                                >
                                                    <div className="text-sm uppercase tracking-[0.18em] text-slate-500">
                                                        {trait} logits
                                                    </div>
                                                    <div className="mt-2 text-3xl font-semibold text-slate-100">
                                                        {formatScore(value)}
                                                    </div>
                                                </div>
                                            ))}
                                        </div>
                                    </>
                                ) : (
                                    <div className="rounded-lg border border-slate-700 bg-slate-950 p-6 text-slate-400">
                                        Nhập text và nhấn Predict để xem kết quả trên biểu đồ.
                                    </div>
                                )}
                            </div>

                            <div className="rounded-lg flex-1 flex flex-col gap-4">
                                <div className="rounded-lg flex-1">
                                    <SentimentChart sentiment={multitaskResult?.sentiment} />
                                </div>
                                <div className="rounded-lg flex w-full gap-4">
                                    <div className="rounded-lg flex-1">
                                        <HelpfulnessCard helpfulness={multitaskResult?.helpfulness} />
                                    </div>
                                    <div className="rounded-lg flex-1">
                                        <ClusterCard
                                            className=""
                                            cluster={clusterLabel || (clusterId != null ? `Cụm ${clusterId}` : "-")}
                                            description={clusterLabel ? "" : ""}
                                        />
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </main>
            </div>
        </div>
    );
}
