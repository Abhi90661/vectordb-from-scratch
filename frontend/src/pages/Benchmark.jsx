import { useState } from "react";
import {
    ResponsiveContainer,
    BarChart,
    Bar,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
} from "recharts";
import api from "../api/api";

import Navbar from "../components/Navbar";
import Sidebar from "../components/Sidebar";

export default function Benchmark() {

    const [results, setResults] = useState([]);
    const [loading, setLoading] = useState(false);

    const fastest =
    results.length > 0
        ? results.reduce((a, b) =>
              a.avg_time_ms < b.avg_time_ms ? a : b
          )
        : null;

const slowest =
    results.length > 0
        ? results.reduce((a, b) =>
              a.avg_time_ms > b.avg_time_ms ? a : b
          )
        : null;

    async function runBenchmark() {

        setLoading(true);

        try {

            const { data } = await api.get("/benchmark");
            setResults(data);

        } catch (err) {

            console.error(err);

        }

        setLoading(false);
    }

    return (

        <div className="h-screen bg-slate-950 text-white">

            <Navbar />

            <div className="flex h-[calc(100vh-64px)]">

                <Sidebar />

                <main className="flex-1 p-8 overflow-y-auto field">

                    <h1 className="text-3xl font-display font-semibold mb-6 text-slate-100">
                        Benchmark
                    </h1>

                    <button
                        onClick={runBenchmark}
                        disabled={loading}
                        className="bg-cyan-500 hover:bg-cyan-600 disabled:bg-slate-600 px-5 py-2 rounded font-semibold mb-6"
                    >
                        {loading ? "Running Benchmark..." : "Run Benchmark"}
                    </button>

                    {results.length > 0 && (

<div className="grid grid-cols-3 gap-6 mb-8">

    <div className="bg-slate-900 rounded-xl p-6 border border-slate-700">

        <h2 className="text-slate-400 text-sm">
            🏆 Fastest Algorithm
        </h2>

        <h1 className="text-3xl font-bold text-cyan-400 mt-2">
            {fastest.algorithm}
        </h1>

        <p className="mt-2">
            {fastest.avg_time_ms} ms
        </p>

    </div>

    <div className="bg-slate-900 rounded-xl p-6 border border-slate-700">

        <h2 className="text-slate-400 text-sm">
            🐢 Slowest Algorithm
        </h2>

        <h1 className="text-3xl font-bold text-red-400 mt-2">
            {slowest.algorithm}
        </h1>

        <p className="mt-2">
            {slowest.avg_time_ms} ms
        </p>

    </div>

    <div className="bg-slate-900 rounded-xl p-6 border border-slate-700">

        <h2 className="text-slate-400 text-sm">
            📦 Algorithms Tested
        </h2>

        <h1 className="text-3xl font-bold text-green-400 mt-2">
            {results.length}
        </h1>

    </div>

</div>

)}


                    

                    





                    {results.length === 0 && !loading && (
                        <div className="text-slate-400">
                            Click "Run Benchmark" to compare all indexing algorithms.
                        </div>
                    )}

                    
                    

                    {results.length > 0 && (

<div className="bg-slate-900 rounded-xl p-6 mb-8">

    <h2 className="text-xl font-bold mb-6">
        Search Time Comparison
    </h2>

    <div className="h-80">

        <ResponsiveContainer width="100%" height="100%">

            <BarChart
                data={results}
            >

                <CartesianGrid stroke="#334155" />

                <XAxis
                    dataKey="algorithm"
                    stroke="#94a3b8"
                />

                <YAxis
                    stroke="#94a3b8"
                    label={{
                        value: "Milliseconds",
                        angle: -90,
                        position: "insideLeft",
                        fill: "#94a3b8",
                    }}
                />

                <Tooltip
                    contentStyle={{
                        backgroundColor: "#0f172a",
                        border: "1px solid #334155",
                        color: "white",
                    }}
                />

                <Bar
                    dataKey="avg_time_ms"
                    fill="#22d3ee"
                    radius={[6, 6, 0, 0]}
                />

            </BarChart>

        </ResponsiveContainer>

    </div>

</div>

)}


{results.length > 0 && (

<div className="bg-slate-900 rounded-xl p-6 mb-8">

    <h2 className="text-xl font-bold mb-6">
        Distance Computations
    </h2>

    <div className="h-80">

        <ResponsiveContainer width="100%" height="100%">

            <BarChart data={results}>

                <CartesianGrid stroke="#334155" />

                <XAxis
                    dataKey="algorithm"
                    stroke="#94a3b8"
                />

                <YAxis
                    stroke="#94a3b8"
                />

                <Tooltip
                    contentStyle={{
                        backgroundColor: "#0f172a",
                        border: "1px solid #334155",
                        color: "white",
                    }}
                />

                <Bar
                    dataKey="distance_computations"
                    fill="#10b981"
                    radius={[6, 6, 0, 0]}
                />

            </BarChart>

        </ResponsiveContainer>

    </div>

</div>

)}



                    



                    {results.length > 0 && (

                    <div className="mt-8">

                        <table className="w-full rounded-xl overflow-hidden border border-slate-700">

                            <thead className="bg-slate-800">

                                <tr>
                                    <th className="p-3">Algorithm</th>
                                    <th>Avg Time (ms)</th>
                                    <th>Distance</th>
                                    <th>Vectors</th>
                                    <th>Clusters</th>
                                    <th>Visited</th>
                                    <th>Layers</th>
                                </tr>

                            </thead>

                            <tbody>

                                {results.map((r) => (

                                    <tr
                                        key={r.algorithm}
                                        className="border-t border-slate-700 text-center hover:bg-slate-800 transition"
                                    >

                                        <td className="p-3">{r.algorithm}</td>
                                        <td>{r.avg_time_ms}</td>
                                        <td>{r.distance_computations}</td>
                                        <td>{r.vectors_scanned}</td>
                                        <td>{r.clusters_scanned}</td>
                                        <td>{r.visited_nodes}</td>
                                        <td>{r.layers_traversed}</td>

                                    </tr>

                                ))}

                            </tbody>

                        </table>

                        </div>

                    )}

                </main>

            </div>

        </div>

    );
}