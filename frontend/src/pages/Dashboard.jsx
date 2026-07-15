import { useEffect, useState } from "react";

import api from "../api/api";

import Navbar from "../components/Navbar";
import Sidebar from "../components/Sidebar";
import StatsCard from "../components/StatsCard";
import SearchBar from "../components/SearchBar";
import ResultsTable from "../components/ResultsTable";

export default function Dashboard() {

    const [stats, setStats] = useState({
        vectors: 0,
        index: "BruteForce",
        dimensions: "-",
        memory: "-"
    });

    const [results, setResults] = useState([]);

    useEffect(() => {

        async function loadStats() {

            try {

                const { data } = await api.get("/stats");

                setStats({
                    vectors: data.total_vectors,
                    index: data.index_type,
                    dimensions: data.dimensions,
                    memory: data.memory_usage,
                });

            } catch (err) {

                console.error(err);

            }

        }

        loadStats();

    }, []);

    async function handleSearch(query, k, metric) {

    try {

        const vector = query
            .split(",")
            .map(Number);

        const { data } = await api.post("/search", {
            query: vector,
            k: Number(k),
            metric,
        });

        setResults(data);

    } catch (err) {

        console.error(err);

    }

}

    return (

        <div className="h-screen bg-slate-950 text-white">

            <Navbar />

            <div className="flex h-[calc(100vh-64px)]">

                <Sidebar />

                <main className="flex-1 p-8 overflow-y-auto field">

                    <h1 className="text-3xl font-display font-semibold mb-1 text-slate-100">
                        Dashboard
                    </h1>
                    <p className="text-sm text-slate-400 mb-8">
                        Live state of the vector store and active index.
                    </p>

                    <div className="grid grid-cols-4 gap-6">

                        <StatsCard
                            title="Vectors"
                            value={stats.vectors}
                        />

                        <StatsCard
                            title="Current Index"
                            value={stats.index}
                        />

                        <StatsCard
                            title="Dimensions"
                            value={stats.dimensions}
                        />

                        <StatsCard
                            title="Memory"
                            value={stats.memory}
                        />

                    </div>

                    <SearchBar onSearch={handleSearch} />

<ResultsTable results={results} />

                </main>

            </div>

        </div>

    );

}