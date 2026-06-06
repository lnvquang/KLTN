"use client";

import "./PersonalityRadar.css";

import {
    RadarChart,
    PolarGrid,
    PolarAngleAxis,
    PolarRadiusAxis,
    Radar,
    Tooltip,
} from "recharts";

export default function PersonalityRadar({
    data,
}) {
    const chartData = [
        {
            trait: "Open",
            value: data.openness,
        },
        {
            trait: "Cons",
            value: data.conscientiousness,
        },
        {
            trait: "Extra",
            value: data.extraversion,
        },
        {
            trait: "Agree",
            value: data.agreeableness,
        },
        {
            trait: "Neuro",
            value: data.neuroticism,
        },
    ];

    return (
        <div className="radar-card">
            <h2 className="radar-title">
                Personality Analysis
            </h2>

            <div className="chart-wrapper">
                <RadarChart width={600} height={400} data={chartData}>

                    <PolarGrid
                        stroke="#bdc2ff"
                        strokeWidth={1}
                        strokeOpacity={0.2}
                        gridType="circle"
                        radialLines={true}
                    />

                    <PolarAngleAxis
                        dataKey="trait"
                        tick={{
                            fill: '#b7c8e1',
                            fontSize: 20,
                            fontWeight: 700,
                        }}
                    />

                    <PolarRadiusAxis 
                        domain={[0, 1]} 
                        ticks={[0, 0.25, 0.5, 0.75, 1]} 
                        tick={false} 
                        axisLine={false}
                    />

                    <Radar
                        stroke="#bdc2ff"
                        strokeWidth={5}
                        dataKey="value"
                        fill="#b7c8e1"
                        fillOpacity={0.4}
                        dot
                    />
                </RadarChart>
            </div>
        </div>
    );
}