import RAGDemo from "./pages/RAGDemo";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import Search from "./pages/Search";
import Dashboard from "./pages/Dashboard";
import Vectors from "./pages/Vectors";
import Visualization from "./pages/Visualization";
import Benchmark from "./pages/Benchmark";

export default function App() {

    return (

        <BrowserRouter>

            <Routes>

                <Route path="/" element={<Dashboard />} />

                <Route path="/vectors" element={<Vectors />} />

                <Route
                    path="/visualization"
                    element={<Visualization />}
                />

                <Route
    path="/benchmark"
    element={<Benchmark />}

/>
                <Route
    path="/search"
    element={<Search />}
/>

<Route
    path="/rag"
    element={<RAGDemo />}
/>

            </Routes>

        </BrowserRouter>

    );

}