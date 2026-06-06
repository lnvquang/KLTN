"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useMemo, useState } from "react";

import { Button } from "@/components/ui/button";
import { getDetailUser } from "@/app/service/api/admin";

function formatDateTime(value) {
    const date = new Date(value);
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

function FieldRow({ label, value }) {
    return (
        <div className="flex items-start justify-between gap-4 border-b border-slate-900 py-3">
            <div className="text-sm text-slate-400">{label}</div>
            <div className="text-sm font-medium text-slate-100">{value}</div>
        </div>
    );
}

export default function AdminUserDetailPage() {
    const params = useParams();
    const idParam = params?.id;
    const userId = useMemo(() => {
        const raw = Array.isArray(idParam) ? idParam[0] : idParam;
        const n = Number(raw);
        return Number.isFinite(n) ? n : null;
    }, [idParam]);

    const [loading, setLoading] = useState(true);
    const [error, setError] = useState("");
    const [user, setUser] = useState(null);
    const [status, setStatus] = useState(true);

    useEffect(() => {
        let cancelled = false;

        async function load() {
            if (userId == null) {
                setLoading(false);
                setError("User id không hợp lệ");
                setUser(null);
                return;
            }

            setLoading(true);
            setError("");
            try {
                const detail = await getDetailUser(userId);
                if (cancelled) return;
                setUser(detail || null);
                setStatus(Boolean(detail?.status ?? true));
            } catch (err) {
                if (cancelled) return;
                const message = err?.response?.data?.message || err?.message || "Lỗi không xác định";
                setError(message);
                setUser(null);
            } finally {
                if (!cancelled) setLoading(false);
            }
        }

        load();
        return () => {
            cancelled = true;
        };
    }, [userId]);

    if (loading) {
        return (
            <div className="space-y-4">
                <h2 className="text-2xl font-semibold text-slate-100">Chi tiết user</h2>
                <div className="text-sm text-slate-400">Đang tải...</div>
            </div>
        );
    }

    if (!user) {
        return (
            <div className="space-y-4">
                <h2 className="text-2xl font-semibold text-slate-100">Không tìm thấy user</h2>
                {error ? (
                    <div className="text-sm text-red-300">{error}</div>
                ) : null}
                <Link href="/admin/users">
                    <Button variant="outline" size="sm">Quay lại</Button>
                </Link>
            </div>
        );
    }

    const fullName = [user.firstName, user.lastName].filter(Boolean).join(" ");
    const reviewsOfUser = (Array.isArray(user?.reviews) ? user.reviews : [])
        .slice()
        .sort((a, b) => {
            const ta = new Date(a?.createdAt).getTime();
            const tb = new Date(b?.createdAt).getTime();
            if (Number.isNaN(ta) && Number.isNaN(tb)) return 0;
            if (Number.isNaN(ta)) return 1;
            if (Number.isNaN(tb)) return -1;
            return tb - ta;
        });

    return (
        <div className="space-y-6">
            <div className="flex flex-wrap items-end justify-between gap-3">
                <div>
                    <h2 className="text-2xl font-semibold text-slate-100">Chi tiết user</h2>
                   
                </div>
                <div className="flex flex-wrap gap-2">
                    <Button
                        variant="destructive"
                        size="sm"
                        onClick={() => setStatus((v) => !v)}
                    >
                        {status ? "Khóa user" : "Mở khóa user"}
                    </Button>
                    <Link href="/admin/users">
                        <Button variant="outline" size="sm">Quay lại</Button>
                    </Link>
                </div>
            </div>

            {error ? (
                <div className="rounded-lg border border-red-500 bg-red-500/10 px-4 py-3 text-sm text-red-200">
                    {error}
                </div>
            ) : null}

            <section className="rounded-xl border border-slate-700 bg-slate-950 p-5">
                <div className="mb-4">
                    <div className="text-lg font-semibold text-slate-100">{fullName}</div>
                    <div className="text-sm text-slate-400">User #{user.id}</div>
                </div>

                <FieldRow label="Email" value={user.email} />
                <FieldRow label="Phone" value={user.phone} />
                <FieldRow label="Role" value={user.role} />
                <FieldRow label="Status" value={status ? "Active" : "Locked"} />
                <FieldRow label="CreatedAt" value={formatDateTime(user.createdAt)} />
            </section>

            <section className="rounded-xl border border-slate-700 bg-slate-950 p-5">
                <div className="flex items-center justify-between gap-4">
                    <h3 className="text-lg font-semibold text-slate-100">Reviews của user</h3>
                    <div className="text-sm text-slate-400">{reviewsOfUser.length} bản ghi (API)</div>
                </div>

                {reviewsOfUser.length === 0 ? (
                    <div className="mt-4 rounded-lg border border-slate-800 bg-slate-900/40 p-4 text-sm text-slate-400">
                        Chưa có review cho user này.
                    </div>
                ) : (
                    <div className="mt-4 grid gap-3">
                        {reviewsOfUser.map((r) => (
                            <div
                                key={r?.id ?? r?.createdAt ?? r?.reviewText}
                                className="rounded-lg border border-slate-800 bg-slate-900/40 p-4"
                            >
                                {(() => {
                                    const clusterLabel = r?.clusterLabel ?? r?.cluster_label;
                                    const clusterId = r?.clusterId ?? r?.cluster;
                                    return (
                                        <div className="mb-2 text-xs text-slate-400">
                                            Cụm: {clusterLabel || (clusterId != null ? `Cụm ${clusterId}` : "-")}
                                        </div>
                                    );
                                })()}
                                <div className="flex flex-wrap items-center justify-between gap-3">
                                    <div className="text-sm text-slate-400">
                                        Review #{r?.id} · {formatDateTime(r?.createdAt)} · Positive: {Math.round(normalize01(r?.sentimentPositive) * 100)}%
                                    </div>
                                    <Link href={`/admin/reviews/${r.id}`}>
                                        <Button variant="outline" size="sm">Xem chi tiết</Button>
                                    </Link>
                                </div>
                                <div className="mt-2 whitespace-pre-wrap text-slate-100">
                                    {r.reviewText}
                                </div>

                                <div className="mt-4">
                                    <div className="flex items-center justify-between text-xs">
                                        <span className="text-slate-300">Sentiment Positive</span>
                                        <span className="text-green-300">
                                            {Math.round(normalize01(r?.sentimentPositive) * 100)}%
                                        </span>
                                    </div>
                                    <div className="mt-2 h-2 w-full rounded-full bg-slate-800">
                                        <div
                                            className="h-2 rounded-full bg-green-500"
                                            style={{
                                                width: `${Math.round(normalize01(r?.sentimentPositive) * 100)}%`,
                                            }}
                                        />
                                    </div>
                                </div>
                            </div>
                        ))}
                    </div>
                )}
            </section>
        </div>
    );
}
