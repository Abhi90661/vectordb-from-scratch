export default function Navbar() {
  return (
    <nav className="h-16 bg-slate-900 border-b border-slate-800 flex items-center justify-between px-8">
      <div className="flex items-center gap-3">
        <span className="relative flex h-2.5 w-2.5">
          <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-cyan-400 opacity-60" />
          <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-cyan-400" />
        </span>

        <h1 className="text-xl font-display font-semibold tracking-tight text-slate-300">
          VectorDB<span className="text-cyan-400">.</span>Engine
        </h1>
      </div>

      <div className="text-xs font-mono text-slate-400 tracking-wide">
        FASTAPI · REACT · NUMPY — NO EXTERNAL ANN LIBRARIES
      </div>
    </nav>
  );
}
