import axios from "axios";

// VITE_API_URL should be set in the frontend's deployment environment
// (e.g. a Vercel env var) to point at the deployed backend. Falls back to
// localhost so `npm run dev` still works out of the box with no setup.
// Previously this was hardcoded to http://127.0.0.1:8000, which meant the
// built frontend would still try to call localhost even once deployed.
const api = axios.create({
    baseURL: import.meta.env.VITE_API_URL || "http://127.0.0.1:8000",
});

export default api;