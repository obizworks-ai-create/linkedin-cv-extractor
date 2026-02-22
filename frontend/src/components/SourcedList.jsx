export default function SourcedList({ candidates }) {
    if (!candidates || candidates.length === 0) {
        return (
            <div className="text-center py-16 text-slate-600 glass-card border-dashed">
                <div className="text-4xl mb-3 opacity-50">🌐</div>
                <p className="text-sm">No candidates sourced yet.</p>
                <p className="text-xs mt-1 text-slate-700">Start an analysis to begin sourcing.</p>
            </div>
        )
    }

    return (
        <div className="space-y-2">
            {candidates.map((cand, i) => (
                <div
                    key={i}
                    className="glass-card-hover p-4 flex items-center gap-4 animate-fade-in group"
                    style={{ animationDelay: `${i * 60}ms` }}
                >
                    {/* Index */}
                    <div className="w-7 h-7 bg-slate-800 rounded-lg flex items-center justify-center text-slate-500 text-xs font-bold shrink-0">
                        {i + 1}
                    </div>

                    {/* Avatar */}
                    <div className="w-10 h-10 bg-gradient-to-br from-slate-700 to-slate-800 rounded-xl flex items-center justify-center text-slate-400 font-bold text-sm shrink-0 group-hover:from-brand-600 group-hover:to-purple-600 group-hover:text-white transition-all duration-300">
                        {(cand.name || '?')[0].toUpperCase()}
                    </div>

                    {/* Info */}
                    <div className="min-w-0 flex-1">
                        <h4 className="font-semibold text-slate-200 text-sm truncate group-hover:text-brand-400 transition-colors">
                            {cand.name || 'Unknown'}
                        </h4>
                        <p className="text-xs text-slate-500 truncate mt-0.5">{cand.headline || 'No headline'}</p>
                    </div>

                    {/* Badges + Link */}
                    <div className="flex items-center gap-2 shrink-0">
                        {cand.is_open_to_work && (
                            <span className="badge bg-emerald-500/15 text-emerald-400 border border-emerald-500/20">
                                ✓ Open to Work
                            </span>
                        )}
                        {cand.profile_url && (
                            <a
                                href={cand.profile_url}
                                target="_blank"
                                rel="noreferrer"
                                className="flex items-center gap-1.5 text-xs font-medium text-brand-400 hover:text-brand-300 bg-brand-500/10 hover:bg-brand-500/20 px-3 py-1.5 rounded-lg border border-brand-500/20 transition-all"
                            >
                                <svg className="w-3.5 h-3.5" viewBox="0 0 24 24" fill="currentColor">
                                    <path d="M19 0h-14c-2.761 0-5 2.239-5 5v14c0 2.761 2.239 5 5 5h14c2.762 0 5-2.239 5-5v-14c0-2.761-2.238-5-5-5zm-11 19h-3v-11h3v11zm-1.5-12.268c-.966 0-1.75-.79-1.75-1.764s.784-1.764 1.75-1.764 1.75.79 1.75 1.764-.783 1.764-1.75 1.764zm13.5 12.268h-3v-5.604c0-3.368-4-3.113-4 0v5.604h-3v-11h3v1.765c1.396-2.586 7-2.777 7 2.476v6.759z" />
                                </svg>
                                LinkedIn
                            </a>
                        )}
                    </div>
                </div>
            ))}
        </div>
    )
}
