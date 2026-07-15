import { Link, useLocation } from "react-router-dom";
import {
  FiGrid,
  FiDatabase,
  FiTarget,
  FiBarChart2,
  FiSearch,
  FiMessageSquare,
} from "react-icons/fi";

const LINKS = [
  { to: "/", label: "Dashboard", icon: FiGrid },
  { to: "/vectors", label: "Vector Explorer", icon: FiDatabase },
  { to: "/visualization", label: "PCA Visualization", icon: FiTarget },
  { to: "/benchmark", label: "Benchmark", icon: FiBarChart2 },
  { to: "/search", label: "Search Playground", icon: FiSearch },
  { to: "/rag", label: "RAG Demo", icon: FiMessageSquare },
];

export default function Sidebar() {
  const location = useLocation();

  return (
    <aside className="w-64 bg-slate-900 border-r border-slate-800 p-6 flex flex-col">
      <h2 className="text-xl font-display font-semibold mb-1 text-slate-300">
        VectorDB
      </h2>
      <p className="text-xs font-mono text-slate-400 mb-8 tracking-wide">
        v0.4 · local-first
      </p>

      <nav className="flex flex-col gap-1">
        {LINKS.map(({ to, label, icon: Icon }) => {
          const active = location.pathname === to;

          return (
            <Link
              key={to}
              to={to}
              className={`flex items-center gap-3 px-3 py-2.5 rounded-md text-sm transition-colors border-l-2 ${
                active
                  ? "bg-slate-800 border-cyan-400 text-slate-100"
                  : "border-transparent text-slate-400 hover:bg-slate-800 hover:text-slate-200"
              }`}
            >
              <Icon
                className={active ? "text-cyan-400" : "text-slate-400"}
                size={16}
              />
              {label}
            </Link>
          );
        })}
      </nav>
    </aside>
  );
}
