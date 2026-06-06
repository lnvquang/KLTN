"use client";

import { PieChart, Pie, Cell, Legend, Tooltip, ResponsiveContainer } from "recharts";

export default function SentimentChart({ sentiment }) {
    if (!sentiment) {
        return <div className="text-slate-400">Không có dữ liệu sentiment</div>;
    }

    const { negative = 0, neutral = 0, positive = 0 } = sentiment;

    const data = [
        { name: "Negative", value: Math.round(negative * 100), color: "#ef4444" },
        { name: "Neutral", value: Math.round(neutral * 100), color: "#f1c40f" },
        { name: "Positive", value: Math.round(positive * 100), color: "#2ecc71" },
    ];

    const filteredData = data.filter((d) => d.value > 0);

    return (
       
        <div className="w-full h-fit flex flex-col items-center justify-center bg-slate-950/40 rounded-xl border border-slate-700/50 p-6">
            
            <h2 className="text-xl font-bold mb-4 text-white">Sentiment Distribution</h2>
            
            {filteredData.length > 0 ? (
               
                <div className="w-full h-[280px]"> 
                    <ResponsiveContainer width="100%" height="100%">
                        <PieChart>
                            <Pie
                                data={filteredData}
                                cx="50%"
                                cy="50%"
                                innerRadius="50%"
                                outerRadius="75%"
                                paddingAngle={2}
                                dataKey="value"
                                stroke="none"
                            >
                                {filteredData.map((entry, index) => (
                                    <Cell key={`cell-${index}`} fill={entry.color} />
                                ))}
                            </Pie>
                            <Tooltip formatter={(value) => `${value}%`} />
                            <Legend verticalAlign="bottom" height={36} />
                        </PieChart>
                    </ResponsiveContainer>
                </div>
            ) : (
                <div className="text-slate-400 text-center py-20">
                    Không có sentiment data để hiển thị
                </div>
            )}

            {/* Summary stats */}
            <div className="mt-6 grid grid-cols-3 gap-4 w-full">
                <div className="flex flex-col items-center p-3 rounded-lg bg-slate-900/50 border border-red-500/20">
                    <div className="text-sm text-slate-400 mb-1">Negative</div>
                    <div className="text-xl font-bold text-red-500">{Math.round(negative * 100)}%</div>
                </div>
                <div className="flex flex-col items-center p-3 rounded-lg bg-slate-900/50 border border-yellow-500/20">
                    <div className="text-sm text-slate-400 mb-1">Neutral</div>
                    <div className="text-xl font-bold text-yellow-500">{Math.round(neutral * 100)}%</div>
                </div>
                <div className="flex flex-col items-center p-3 rounded-lg bg-slate-900/50 border border-green-500/20">
                    <div className="text-sm text-slate-400 mb-1">Positive</div>
                    <div className="text-xl font-bold text-green-500">{Math.round(positive * 100)}%</div>
                </div>
            </div>
        </div>
    );
}