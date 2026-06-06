import { Smile, Meh, Frown } from "lucide-react";
import './ClusterCard.css'
export default function SentimentCard({
    sentiment,
}) {
    const sentimentMap = {
        0: {
            label: "Negative",
            icon: <Frown size={100} color="#e74c3c" />
        },
        1: {
            label: "Neutral",
            icon: <Meh size={100} color="#f1c40f" />

        },
        2: {
            label: "Positive",
            icon: <Smile size={100} color="#2ecc71" />
        }
    };
    return (
        <div className="card p-4 h-full ">
            <h1 className="text-2xl font-bold mb-2">Sentiment</h1>

            <div className="flex items-center justify-center h-[150px]">
                {sentimentMap[sentiment]?.icon}
            </div>
            <p className="text-lg font-semibold text-center">
                {sentimentMap[sentiment]?.label}
            </p>
        </div>
    );
}