"use client";

import {
    ResponsiveContainer,
    LineChart,
    Line,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
} from "recharts";

function formatDateLabel(yyyyMmDd) {
    if (!yyyyMmDd) return "-";
    const parts = yyyyMmDd.split("-");
    if (parts.length !== 3) return yyyyMmDd;
    return `${parts[2]}/${parts[1]}`;
}

function ReviewsTooltip({ active, payload }) {
    if (!active || !payload?.length) return null;
    const point = payload[0]?.payload;
    if (!point) return null;

    return (
        <div className="rounded-xl border border-slate-700 bg-slate-900/95 px-4 py-3 text-slate-100 shadow-xl">
            <div className="text-sm font-semibold">{formatDateLabel(point.date)}</div>
            <div className="mt-2 flex items-center gap-2 text-sm">
                <span className="inline-block h-2.5 w-2.5 rounded-full bg-sky-500" />
                <span className="text-slate-300">Reviews</span>
                <span className="ml-2 font-semibold text-slate-100">{point.count}</span>
            </div>
        </div>
    );
}

export default function ReviewCountByDayChart({ items }) {
    if (!Array.isArray(items) || items.length === 0) {
        return <div className="text-slate-400">Không có dữ liệu review theo ngày</div>;
    }

    // Accept multiple shapes:
    // - [{ date: 'YYYY-MM-DD', count: 12 }]
    // - [{ day: 'YYYY-MM-DD', total: 12 }]
    // - Raw reviews [{ createdAt: '...' }, ...] => auto-group by day
    const counts = new Map();
    for (const r of items) {
        const explicitDate = r?.date || r?.day;
        const explicitCount = r?.count ?? r?.total ?? r?.reviews;

        if (explicitDate && typeof explicitCount === "number") {
            const dayKey = String(explicitDate).slice(0, 10);
            counts.set(dayKey, (counts.get(dayKey) || 0) + explicitCount);
            continue;
        }

        const createdAt = r?.createdAt;
        if (!createdAt) continue;
        const dayKey = String(createdAt).slice(0, 10);
        counts.set(dayKey, (counts.get(dayKey) || 0) + 1);
    }

    const data = Array.from(counts.entries())
        .sort((a, b) => (a[0] > b[0] ? 1 : -1))
        .map(([date, count]) => ({ date, label: formatDateLabel(date), count }));

    return (
        <div className="w-full rounded-lg border border-slate-700 bg-slate-950 p-4">
            <div className="mb-4">
                <h2 className="text-xl font-semibold text-white">Số lượng đánh giá theo ngày</h2>
                <p className="mt-1 text-sm text-slate-400">Tổng số review được tạo mỗi ngày.</p>
            </div>

            <ResponsiveContainer width="100%" height={320}>
                <LineChart data={data} margin={{ top: 10, right: 16, left: 0, bottom: 10 }}>
                    <CartesianGrid strokeDasharray="4 4" stroke="#334155" opacity={0.35} />
                    <XAxis
                        dataKey="label"
                        tick={{ fill: "#cbd5e1" }}
                        axisLine={false}
                        tickLine={false}
                    />
                    <YAxis
                        allowDecimals={false}
                        tick={{ fill: "#94a3b8" }}
                        axisLine={false}
                        tickLine={false}
                        domain={[0, (max) => Math.ceil((max || 0) + 2)]}
                    />
                    <Tooltip content={<ReviewsTooltip />} cursor={{ stroke: "#334155", opacity: 0.6 }} />
                    <Line
                        type="monotone"
                        dataKey="count"
                        stroke="#0284c7"
                        strokeWidth={2.5}
                        dot={false}
                        activeDot={{ r: 5, fill: "#0ea5e9", stroke: "#0b1220", strokeWidth: 2 }}
                    />
                </LineChart>
            </ResponsiveContainer>
        </div>
    );
}
