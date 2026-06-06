"use client";

import {
    ResponsiveContainer,
    BarChart,
    Bar,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
} from "recharts";
import { BarChart3 } from "lucide-react";

function toNumber(value) {
    if (typeof value !== "number" || Number.isNaN(value)) return 0;
    return value;
}

export default function BigFiveAverageBarChart({ values }) {
    if (!values) {
        return (
            <div className="flex min-h-[300px] w-full flex-col items-center justify-center rounded-xl border border-zinc-800 bg-zinc-950 p-6 text-slate-400 shadow-sm">
                <BarChart3 className="mb-2 h-8 w-8 text-zinc-600" />
                <span className="text-sm font-medium">Chưa có dữ liệu Big Five</span>
            </div>
        );
    }

    const data = [
        { name: "Openness", value: toNumber(values.openness) },
        { name: "Conscientiousness", value: toNumber(values.conscientiousness) },
        { name: "Extraversion", value: toNumber(values.extraversion) },
        { name: "Agreeableness", value: toNumber(values.agreeableness) },
        { name: "Neuroticism", value: toNumber(values.neuroticism) },
    ];

    const CustomTooltip = ({ active, payload, label }) => {
        if (active && payload && payload.length) {
            return (
                <div className="rounded-lg border border-zinc-700 bg-zinc-900 px-3 py-2 shadow-xl outline-none">
                    <p className="mb-1 text-xs font-semibold uppercase tracking-wider text-slate-400">
                        {label}
                    </p>
                    <p className="text-sm font-bold text-indigo-400">
                        Trung bình: <span className="text-slate-100">{Number(payload[0].value).toFixed(2)}</span>
                    </p>
                </div>
            );
        }
        return null;
    };

    return (
        <div className="flex h-fit w-full flex-col rounded-xl border border-zinc-800/80 bg-zinc-950/50 p-5 shadow-sm">
            <div className="mb-6">
                <h2 className="text-lg font-semibold tracking-tight text-slate-100">
                    Chỉ số Big Five (OCEAN)
                </h2>
                <p className="mt-0.5 text-xs text-slate-400">
                    Giá trị trung bình của 5 nhóm tính cách.
                </p>
            </div>

            {/* Tăng chiều cao container một chút để cân đối với chữ bự hơn */}
            <div className="w-full h-[360px]">
                <ResponsiveContainer width="100%" height="100%">
                    <BarChart 
                        data={data} 
                        // TĂNG margin bottom lên 30 để SVG không cắt đuôi chữ
                        margin={{ top: 10, right: 10, left: -20, bottom: 30 }}
                    >
                        <CartesianGrid strokeDasharray="3 3" stroke="#27272a" vertical={false} />
                        
                        <XAxis 
                            dataKey="name" 
                            // TĂNG fontSize lên 13 hoặc 14 để dễ đọc hơn
                            tick={{ fill: "#a1a1aa", fontSize: 13.5 }} 
                            axisLine={false}
                            tickLine={false}
                            interval={0} 
                            angle={-40} 
                            textAnchor="end"
                         
                            height={90}
                            dx={-5} 
                        />
                        
                        <YAxis 
                            domain={[0, 1]} 
                            tick={{ fill: "#71717a", fontSize: 13 }} 
                            axisLine={false}
                            tickLine={false}
                            tickFormatter={(value) => value.toFixed(1)}
                        />
                        
                        <Tooltip content={<CustomTooltip />} cursor={{ fill: '#27272a', opacity: 0.4 }} />
                        
                        <Bar 
                            dataKey="value" 
                            fill="#6366f1" 
                            radius={[6, 6, 0, 0]} 
                            maxBarSize={48}
                            animationDuration={1000}
                        />
                    </BarChart>
                </ResponsiveContainer>
            </div>
        </div>
    );
}