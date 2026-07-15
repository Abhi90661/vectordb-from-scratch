import { useState } from "react";
import api from "../api/api";
import Navbar from "../components/Navbar";
import Sidebar from "../components/Sidebar";

export default function Search() {

    const [query, setQuery] = useState("");

const [k, setK] = useState(5);

const [results, setResults] = useState([]);

const [loading, setLoading] = useState(false);


async function handleSearch() {

    try {

        setLoading(true);

        const vector = query
            .split(",")
            .map(Number);

        const { data } = await api.post("/search", {
            query: vector,
            k: k,
        });

        setResults(data);

    } catch (err) {

        console.error(err);

        alert("Search failed");

    }

    setLoading(false);

}

    return (

        <div className="h-screen bg-slate-950 text-white">

            <Navbar />

            <div className="flex h-[calc(100vh-64px)]">

                <Sidebar />

                <main className="flex-1 p-8 overflow-y-auto field">

                    <h1 className="text-3xl font-display font-semibold mb-8 text-slate-100">
    Search Playground
</h1>

<div className="bg-slate-900 rounded-xl p-6 mb-8">

    <div className="mb-5">

        <label className="block mb-2">
            Query Vector
        </label>

        <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Example: 0.1,0.5,0.3"
            className="w-full bg-slate-800 p-3 rounded"
        />

    </div>

    <div className="mb-5">

        <label className="block mb-2">
            Top K
        </label>

        <input
            type="number"
            value={k}
            onChange={(e) => setK(Number(e.target.value))}
            className="bg-slate-800 p-3 rounded w-32"
        />

    </div>

    <button
    onClick={handleSearch}
    disabled={loading}
    className="bg-cyan-500 hover:bg-cyan-600 disabled:bg-slate-700 px-6 py-3 rounded"
>
    {loading ? "Searching..." : "Search"}
</button>

</div>

{results.length > 0 && (

<div className="bg-slate-900 rounded-xl p-6">

    <h2 className="text-2xl font-bold mb-6">
        Search Results
    </h2>

    <table className="w-full">

        <thead>

            <tr className="border-b border-slate-700">

                <th className="text-left p-3">ID</th>
                <th className="text-left p-3">Distance</th>
                <th className="text-left p-3">Metadata</th>

            </tr>

        </thead>

        <tbody>

            {results.map((r, index) => (

                <tr
                    key={index}
                    className="border-b border-slate-800"
                >

                    <td className="p-3">{r.item.id}</td>

                    <td className="p-3">
                        {r.distance.toFixed(5)}
                    </td>

                    <td className="p-3">
                        {JSON.stringify(r.item.metadata)}
                    </td>

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