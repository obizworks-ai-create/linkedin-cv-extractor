import { useEffect, useRef } from 'react'

export default function LogConsole({ logs }) {
    const endRef = useRef(null)

    useEffect(() => {
        endRef.current?.scrollIntoView({ behavior: 'smooth' })
    }, [logs])

    return (
        <div className="glass-card overflow-hidden font-mono text-xs">
            {/* Titlebar */}
            <div className="bg-slate-800/40 px-4 py-2.5 border-b border-slate-800/50 flex items-center justify-between">
                <div className="flex items-center gap-2">
                    <div className="flex gap-1.5">
                        <div className="w-2.5 h-2.5 rounded-full bg-red-500/60" />
                        <div className="w-2.5 h-2.5 rounded-full bg-amber-500/60" />
                        <div className="w-2.5 h-2.5 rounded-full bg-emerald-500/60" />
                    </div>
                    <span className="text-slate-500 text-[11px] ml-2">pipeline.log</span>
                </div>
                <span className="text-slate-600 text-[10px] uppercase tracking-wider">Live</span>
            </div>

            {/* Log Body */}
            <div className="p-4 h-44 overflow-y-auto space-y-1 text-slate-400">
                {logs.length === 0 && (
                    <span className="text-slate-700 italic">$ awaiting commands...</span>
                )}
                {logs.map((log, i) => (
                    <div
                        key={i}
                        className="border-l-2 border-slate-800 pl-3 py-0.5 animate-fade-in hover:border-brand-500/50 hover:text-slate-200 transition-colors"
                    >
                        {log}
                    </div>
                ))}
                <div ref={endRef} />
            </div>
        </div>
    )
}
