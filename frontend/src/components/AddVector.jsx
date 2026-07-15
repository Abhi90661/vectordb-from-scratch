import { useState } from "react";
import api from "../api/api";

export default function AddVector({ onAdded }) {
  const [id, setId] = useState("");
  const [vector, setVector] = useState("");
  const [metadata, setMetadata] = useState("{}");
  const [error, setError] = useState("");

  async function handleSubmit(e) {
    e.preventDefault();
    setError("");

    let parsedMetadata;
    try {
      parsedMetadata = JSON.parse(metadata);
    } catch {
      setError("Metadata isn't valid JSON — check for a missing quote or brace.");
      return;
    }

    try {
      await api.post("/vectors", {
        id,
        vector: vector.split(",").map(Number),
        metadata: parsedMetadata,
      });

      setId("");
      setVector("");
      setMetadata("{}");

      onAdded();
    } catch (err) {
      setError(
        err.response?.data?.detail || "Failed to insert vector. Check the ID and vector values."
      );
    }
  }

  return (
    <form
      onSubmit={handleSubmit}
      className="bg-slate-900 p-6 rounded-xl mb-8"
    >
      <h2 className="text-xl font-bold mb-4">Insert Vector</h2>

      {error && (
        <div className="bg-red-950 border border-red-700 text-red-300 text-sm p-3 rounded mb-3">
          {error}
        </div>
      )}

      <input
        className="w-full bg-slate-800 p-3 rounded mb-3"
        placeholder="Vector ID"
        value={id}
        onChange={(e) => setId(e.target.value)}
      />

      <input
        className="w-full bg-slate-800 p-3 rounded mb-3"
        placeholder="1,2,3"
        value={vector}
        onChange={(e) => setVector(e.target.value)}
      />

      <textarea
        className="w-full bg-slate-800 p-3 rounded mb-4"
        rows={4}
        value={metadata}
        onChange={(e) => setMetadata(e.target.value)}
      />

      <button className="bg-blue-600 px-6 py-2 rounded">
        Insert
      </button>
    </form>
  );
}