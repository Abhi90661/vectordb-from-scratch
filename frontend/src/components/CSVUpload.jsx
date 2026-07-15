import { useState } from "react";
import api from "../api/api";

export default function CSVUpload({ onUploaded }) {

    const [file, setFile] = useState(null);

    async function upload() {

    if (!file) {
        alert("Please select a CSV file");
        return;
    }

    try {

        const form = new FormData();
        form.append("file", file);

        console.log("Uploading:", file.name);

        const res = await api.post("/upload", form, {
            headers: {
                "Content-Type": "multipart/form-data",
            },
        });

        console.log("Response:", res.data);

        alert("Upload successful!");

        onUploaded();

    } catch (err) {

        console.error(err);

        alert("Upload failed");

    }
}

    return (

        <div className="bg-slate-900 p-6 rounded-xl mb-8">

            <h2 className="text-xl font-bold mb-4">
                Upload CSV
            </h2>

            <input
                type="file"
                accept=".csv"
                onChange={(e)=>setFile(e.target.files[0])}
            />

            <button
                onClick={upload}
                className="bg-green-600 px-5 py-2 rounded ml-4"
            >
                Upload
            </button>

        </div>

    );

}