export default function StatsCard({
    title,
    value,
}) {
    return (
        <div className="relative bg-slate-900 rounded-xl p-6 border border-slate-800 overflow-hidden">

            {/* corner tick, echoing the coordinate-grid motif used across the app */}
            <div className="absolute top-0 right-0 w-8 h-8 border-t border-r border-cyan-700/40 rounded-tr-xl m-2" />

            <p className="text-slate-400 text-xs font-mono tracking-wide uppercase">
                {title}
            </p>

            <h2 className="text-3xl font-display font-semibold mt-3 text-cyan-400 font-mono">
                {value}
            </h2>

        </div>
    );
}
