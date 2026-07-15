import { useEffect, useState } from "react";

import {
    ScatterChart,
    Scatter,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    ResponsiveContainer,
    Legend,
} from "recharts";

import api from "../api/api";
import Navbar from "../components/Navbar";
import Sidebar from "../components/Sidebar";

export default function Visualization() {

    const [points, setPoints] = useState([]);

    const [stats, setStats] = useState({
    total_vectors: 0,
    dimensions: 0,
    explained_variance: 0,
});

    useEffect(() => {

        async function load() {
            try {
                const { data } = await api.get("/pca");
                console.log(data.points[0]);

setPoints(data.points);

setStats({
    total_vectors: data.total_vectors,
    dimensions: data.dimensions,
    explained_variance: data.explained_variance,
});
            } catch (err) {
                console.error(err);
            }
        }

        load();

    }, []);


    const groupedPoints = {};

points.forEach((point) => {

    const category = point.metadata.category || "Unknown";

    if (!groupedPoints[category]) {
        groupedPoints[category] = [];
    }

    groupedPoints[category].push(point);

});


const colors = {
    A: "#3b82f6",   // Blue
    B: "#22c55e",   // Green
    C: "#facc15",   // Yellow
    D: "#ef4444",   // Red
    Unknown: "#94a3b8"
};

    return (

        <div className="h-screen bg-slate-950 text-white">

            <Navbar />

            <div className="flex h-[calc(100vh-64px)]">

                <Sidebar />

                <main className="flex-1 p-8 overflow-y-auto field">

                    <h1 className="text-3xl font-display font-semibold mb-8 text-slate-100">
                        PCA Visualization
                    </h1>

                    <div className="grid grid-cols-4 gap-6 mb-8">

    <div className="bg-slate-900 rounded-xl p-5">

        <p className="text-slate-400 text-sm">
            Total Vectors
        </p>

        <h2 className="text-3xl font-bold mt-2 text-cyan-400 font-mono">
            {stats.total_vectors}
        </h2>

    </div>

    <div className="bg-slate-900 rounded-xl p-5">

        <p className="text-slate-400 text-sm">
            Original Dimensions
        </p>

        <h2 className="text-3xl font-bold mt-2 text-blue-600 font-mono">
            {stats.dimensions}
        </h2>

    </div>

    <div className="bg-slate-900 rounded-xl p-5">

        <p className="text-slate-400 text-sm">
            Reduced Dimensions
        </p>

        <h2 className="text-3xl font-bold mt-2 text-green-400 font-mono">
            2D
        </h2>

    </div>

    <div className="bg-slate-900 rounded-xl p-5">

        <p className="text-slate-400 text-sm">
            Explained Variance
        </p>

        <h2 className="text-3xl font-bold mt-2 text-red-400 font-mono">
            {stats.explained_variance.toFixed(2)}%
        </h2>

    </div>

</div>

                    <div className="bg-slate-900 rounded-xl p-6 h-[600px]">

                        <ResponsiveContainer width="100%" height="100%">

                            <ScatterChart
    margin={{
        top: 20,
        right: 20,
        bottom: 20,
        left: 20,
    }}
>

    <CartesianGrid stroke="#334155" />

    <XAxis
        type="number"
        dataKey="x"
        name="Principal Component 1"
        tickFormatter={(v) => v.toFixed(2)}
        stroke="#94a3b8"
        label={{
            value: "Principal Component 1",
            position: "insideBottom",
            offset: -10,
            fill: "#94a3b8",
        }}
    />

    <YAxis
        type="number"
        dataKey="y"
        name="Principal Component 2"
        tickFormatter={(v) => v.toFixed(2)}
        stroke="#94a3b8"
        label={{
            value: "Principal Component 2",
            angle: -90,
            position: "insideLeft",
            fill: "#94a3b8",
        }}
    />

    <Tooltip
    cursor={{ strokeDasharray: "3 3" }}
    content={({ active, payload }) => {
        if (active && payload && payload.length) {

            const p = payload[0].payload;

            return (
                <div
                    style={{
                        background: "#0f172a",
                        border: "1px solid #334155",
                        padding: "10px",
                        borderRadius: "8px",
                        color: "white",
                    }}
                >
                    <p><strong>ID:</strong> {p.id}</p>
                    <p><strong>PC1:</strong> {p.x.toFixed(2)}</p>
                    <p><strong>PC2:</strong> {p.y.toFixed(2)}</p>
                    <p><strong>Category:</strong> {p.metadata.category}</p>
                </div>
            );
        }

        return null;
    }}
/>

    <Legend
    verticalAlign="top"
    align="center"
    height={50}
/>

    {Object.entries(groupedPoints).map(([category, data]) => (

    <Scatter
        key={category}
        name={`Category ${category}`}
        data={data}
        fill={colors[category] || colors.Unknown}
        shape={(props) => (
            <circle
                cx={props.cx}
                cy={props.cy}
                r={6}
                fill={colors[category] || colors.Unknown}
            />
        )}
    />

))}

</ScatterChart>

                        </ResponsiveContainer>

                    </div>

                </main>

            </div>

        </div>

    );

}