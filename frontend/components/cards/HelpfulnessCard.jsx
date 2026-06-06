import "./ClusterCard.css";

import {
    BadgeCheck,
} from "lucide-react";

export default function HelpfulnessCard({ helpfulness }) {
    if (!helpfulness) {
        return (
            <div className="card p-4 h-full flex flex-col gap-6">
                <div className="text-sm text-zinc-400">Không có dữ liệu helpfulness.</div>
            </div>
        );
    }

    const total = Math.round((helpfulness.total || 0) * 100);

    return (
        <div className="card p-4 h-full flex flex-col gap-6">
            <div className="flex items-center gap-4">
                <div className="rounded-full bg-slate-900 p-3">
                    <BadgeCheck size={32} color="#22c55e" />
                </div>

                <div>
                    <h1 className="text-sm text-zinc-400">Helpfulness</h1>
                    <h2 className="text-xl font-bold text-slate-100">
                        {total}%
                    </h2>
                </div>
            </div>

            <div className="text-sm text-zinc-400 mt-auto">
                Helpfulness total: {total}%
            </div>
        </div>
    );
}