import { useEffect, useState } from "react";
import api from "../api/api";

import Navbar from "../components/Navbar";
import Sidebar from "../components/Sidebar";

export default function RAGDemo() {

    const [file, setFile] = useState(null);
    const [question, setQuestion] = useState("");

    const [messages, setMessages] = useState([]);

    const [chatId, setChatId] = useState(null);

const [chats, setChats] = useState([]);

    const [uploading, setUploading] = useState(false);

    const [loading, setLoading] = useState(false);

    const [algorithm, setAlgorithm] = useState("bruteforce");
    const [switchingAlgorithm, setSwitchingAlgorithm] = useState(false);
    const [benchmark, setBenchmark] = useState(null);

    useEffect(() => {

    async function initializeChat() {

        try {

            const chatsResponse = await api.get("/chat");

            if (chatsResponse.data.length > 0) {

                setChats(chatsResponse.data);

                setChatId(chatsResponse.data[0].id);

            } else {

                const { data } = await api.post("/chat/new");

                setChatId(data.id);

                setChats([data]);

            }

        } catch (err) {

            console.error(err);

        }

    }

    initializeChat();

}, []);

async function createNewChat() {

    try {

        const { data } = await api.post("/chat/new");

        setChatId(data.id);



setQuestion("");
setMessages([]);

        const chatsResponse = await api.get("/chat");

        setChats(chatsResponse.data);

    } catch (err) {

        console.error(err);

    }

}

async function openChat(id) {

    try {

        const { data } = await api.get(`/chat/${id}`);

        setChatId(id);

        const chatsResponse = await api.get("/chat");

setChats(chatsResponse.data);

        const history = [];

        for (let i = 0; i < data.messages.length; i += 2) {

            history.push({

                question: data.messages[i]?.content,

                answer: data.messages[i + 1]?.content,

                // Backend now persists retrieval sources alongside each
                // assistant message (previously this was always []),
                // so reopening a past chat shows its Retrieved Chunks too.
                sources: data.messages[i + 1]?.sources || [],
                benchmark: data.messages[i + 1]?.benchmark,

            });

        }

        setMessages(history);

    } catch (err) {

        console.error(err);

    }

}

async function changeAlgorithm(e) {

    const selected = e.target.value;

    setSwitchingAlgorithm(true);

    try {

        await api.post("/rag/index", {
            index: selected,
        });

        setAlgorithm(selected);

    } catch (err) {

        console.error(err);

        alert("Failed to switch algorithm");

    }

    setSwitchingAlgorithm(false);

}

    async function uploadDocument() {

        if (!file) return;

        const formData = new FormData();

        formData.append("file", file);

        setUploading(true);

        try {

            await api.post(
                "/rag/upload",
                formData,
                {
                    headers: {
                        "Content-Type": "multipart/form-data",
                    },
                }
            );

            alert("Document uploaded successfully");

        } catch (err) {

            console.error(err);

            alert("Upload failed");

        }

        setUploading(false);

    }

    async function askAI() {

        if (!question.trim()) return;

        setLoading(true);

        try {

            const { data } = await api.post(
    "/rag/ask",
    {
        chat_id: chatId,
        question,
        k: 3,
    }
);

setBenchmark(data.benchmark);

            setMessages((prev) => [
    ...prev,
    {
        question: question,
        answer: data.answer,
        sources: data.sources,
        benchmark: data.benchmark,
    },
]);

setQuestion("");

const chatsResponse = await api.get("/chat");

setChats(chatsResponse.data);

        } catch (err) {

            console.error(err);

            alert("Failed");

        }

        setLoading(false);

    }

    return (

        <div className="h-screen bg-slate-950 text-white">

            <Navbar />

            <div className="flex h-[calc(100vh-64px)]">

                <Sidebar />

                <div className="flex flex-1">

    {/* Chat Sidebar */}
    <div className="w-72 bg-slate-900 border-r border-slate-800 p-4">

        <button
    onClick={createNewChat}
    className="w-full bg-cyan-500 hover:bg-cyan-600 rounded-lg py-3 mb-6"
>
    + New Chat
</button>

        <h2 className="text-lg font-bold mb-4">
            Chat History
        </h2>

        <div className="space-y-3">

            {chats.map((chat) => (

                <div
    key={chat.id}
    onClick={() => openChat(chat.id)}
    className={`rounded-lg p-3 cursor-pointer transition hover:bg-slate-700 ${
        chat.id === chatId
            ? "bg-cyan-700"
            : "bg-slate-800"
    }`}
>

                    <p className="font-medium truncate">
                        {chat.title}
                    </p>

                    <p className="text-xs text-slate-400 mt-1">
                        {new Date(chat.created_at).toLocaleString()}
                    </p>

                </div>

            ))}

        </div>

    </div>

    {/* Main Content */}
    <main className="flex-1 p-8 overflow-y-auto field">

                    <div className="flex justify-between items-center mb-8">

    <h1 className="text-3xl font-display font-semibold text-slate-100">
        RAG Demo
    </h1>

</div>

<div className="bg-slate-900 rounded-xl p-6 mb-8">

    <h2 className="text-xl font-bold mb-5">
        Search Algorithm
    </h2>

    <select
        value={algorithm}
        onChange={changeAlgorithm}
        disabled={switchingAlgorithm}
        className="w-full bg-slate-800 rounded p-4"
    >
        <option value="bruteforce">Brute Force</option>
        <option value="kdtree">KD Tree</option>
        <option value="ivf">IVF</option>
        <option value="hnsw">HNSW</option>
    </select>

    <p className="text-slate-400 text-sm mt-3">
        {switchingAlgorithm
            ? "Rebuilding index..."
            : `Current Algorithm: ${algorithm}`}
    </p>

</div>

{benchmark && (

<div className="grid grid-cols-3 gap-6 mb-8">

    <div className="bg-slate-900 rounded-xl p-6 border border-slate-700">

        <p className="text-slate-400 text-sm">
            Algorithm
        </p>

        <h2 className="text-3xl font-bold text-cyan-400 mt-2">
            {benchmark.algorithm}
        </h2>

    </div>

    <div className="bg-slate-900 rounded-xl p-6 border border-slate-700">

        <p className="text-slate-400 text-sm">
            Search Time
        </p>

        <h2 className="text-3xl font-bold text-green-400 mt-2">
            {benchmark.time_ms} ms
        </h2>

    </div>

    <div className="bg-slate-900 rounded-xl p-6 border border-slate-700">

        <p className="text-slate-400 text-sm">
            Indexed Vectors
        </p>

        <h2 className="text-3xl font-bold text-blue-600 mt-2 font-mono">
            {benchmark.vector_count}
        </h2>

    </div>

</div>

)}

<div className="bg-slate-900 rounded-xl p-6 mb-8">

    <h2 className="text-xl font-bold mb-5">
        Upload Document
    </h2>

    <input
        type="file"
        accept=".txt"
        onChange={(e) => setFile(e.target.files[0])}
        className="mb-5 block"
    />

    <button
        onClick={uploadDocument}
        disabled={uploading}
        className="bg-cyan-500 hover:bg-cyan-600 disabled:bg-slate-700 px-6 py-3 rounded"
    >
        {uploading ? "Uploading..." : "Upload"}
    </button>

</div>

<div className="bg-slate-900 rounded-xl p-6 mb-8">

    <h2 className="text-xl font-bold mb-5">
        Ask AI
    </h2>

    <textarea
        rows={4}
        value={question}
        onChange={(e) => setQuestion(e.target.value)}
        placeholder="Ask anything about the uploaded document..."
        className="w-full bg-slate-800 rounded p-4 mb-5"
    />

    <button
        onClick={askAI}
        disabled={loading}
        className="bg-green-500 hover:bg-green-600 disabled:bg-slate-700 px-6 py-3 rounded"
    >
        {loading ? "Thinking..." : "Ask AI"}
    </button>

</div>

{messages.map((chat, index) => (

<div
    key={index}
    className="space-y-6 mb-10"
>

    {/* User Question */}

    <div className="bg-blue-900 rounded-xl p-5">

        <h3 className="text-lg font-bold mb-2">
            👤 You
        </h3>

        <p>
            {chat.question}
        </p>

    </div>

    {/* AI Answer */}

    <div className="bg-slate-900 rounded-xl p-5">

        <h3 className="text-lg font-bold text-green-400 mb-3">
            🤖 AI
        </h3>

        <div className="whitespace-pre-wrap leading-8">
            {chat.answer}
        </div>

        {chat.benchmark && (

<div className="mt-5 flex gap-6 text-sm text-slate-400 border-t border-slate-700 pt-4">

    <span>
        ⚡ {chat.benchmark.algorithm}
    </span>

    <span>
        ⏱ {chat.benchmark.time_ms} ms
    </span>

    <span>
        📦 {chat.benchmark.vector_count} vectors
    </span>

</div>

)}

    </div>

    {/* Sources */}

    <div className="bg-slate-900 rounded-xl p-5">

        <h3 className="text-xl font-bold mb-5">
            Retrieved Chunks
        </h3>

        {chat.sources.map((source, i) => (

            <div
                key={i}
                className="border border-slate-700 rounded-lg p-5 mb-5"
            >

                <h4 className="font-bold text-cyan-400 mb-3">
                    Chunk {i + 1}
                </h4>

                <p className="whitespace-pre-wrap text-slate-300">
                    {source.text}
                </p>

                <div className="mt-4 text-sm text-slate-400">

                    <p>
                        <strong>Source:</strong> {source.source}
                    </p>

                    <p>
                        <strong>Distance:</strong>{" "}
                        {source.distance.toFixed(5)}
                    </p>

                </div>

            </div>

        ))}

    </div>

</div>

))}





                </main>

                </div>

            </div>

        </div>

    );

}