import { useState } from "react";

export default function SearchBar({ onSearch }) {

    const [query, setQuery] = useState("");
    const [k, setK] = useState(5);
    const [metric, setMetric] = useState("cosine");

    return (
        <div className="bg-slate-900 p-5 rounded-xl mt-8">

            <h2 className="text-xl font-bold mb-4">
                Vector Search
            </h2>

            <input
                className="w-full p-3 rounded bg-slate-800 mb-3"
                placeholder="1,2,3"
                value={query}
                onChange={(e)=>setQuery(e.target.value)}
            />

            <div className="flex gap-4">

                <input
                    type="number"
                    className="p-3 rounded bg-slate-800"
                    value={k}
                    onChange={(e)=>setK(e.target.value)}
                />

                <select
                    className="p-3 rounded bg-slate-800"
                    value={metric}
                    onChange={(e)=>setMetric(e.target.value)}
                >
                    <option value="cosine">Cosine</option>
                    <option value="euclidean">Euclidean</option>
                    <option value="manhattan">Manhattan</option>
                </select>

                <button
                    className="bg-blue-600 px-6 rounded"
                    onClick={()=>onSearch(query,k,metric)}
                >
                    Search
                </button>

            </div>

        </div>
    );
}