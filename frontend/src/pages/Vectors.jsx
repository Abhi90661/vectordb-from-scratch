import CSVUpload from "../components/CSVUpload";
import AddVector from "../components/AddVector";
import { useEffect, useState } from "react";
import api from "../api/api";
import Navbar from "../components/Navbar";
import Sidebar from "../components/Sidebar";

export default function Vectors() {
  const [vectors, setVectors] = useState([]);

  useEffect(() => {
    loadVectors();
  }, []);

  async function loadVectors() {
    const { data } = await api.get("/vectors");
    setVectors(data);
  }

  async function deleteVector(id) {
    await api.delete(`/vectors/${id}`);
    loadVectors();
  }

  return (
    <div className="h-screen bg-slate-950 text-white">
      <Navbar />

      <div className="flex h-[calc(100vh-64px)]">
        <Sidebar />

        <main className="flex-1 p-8 overflow-y-auto field">
          <h1 className="text-3xl font-display font-semibold mb-6 text-slate-100">Stored Vectors</h1>

          <AddVector onAdded={loadVectors} />
          <CSVUpload onUploaded={loadVectors} />

          <table className="w-full">
            <thead>
              <tr className="border-b border-slate-700">
                <th className="text-left p-3">ID</th>
                <th className="text-left p-3">Vector</th>
                <th className="text-left p-3">Metadata</th>
                <th className="text-left p-3">Action</th>
              </tr>
            </thead>

            <tbody>
              {vectors.map((v) => (
                <tr key={v.id} className="border-b border-slate-800">
                  <td className="p-3">{v.id}</td>

                  <td className="p-3">
                    [{v.vector.join(", ")}]
                  </td>

                  <td className="p-3">
                    {JSON.stringify(v.metadata)}
                  </td>

                  <td className="p-3">
                    <button
                      onClick={() => deleteVector(v.id)}
                      className="bg-red-600 px-3 py-1 rounded"
                    >
                      Delete
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>

          </table>

        </main>
      </div>
    </div>
  );
}