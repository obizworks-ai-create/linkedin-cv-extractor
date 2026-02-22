export default function WorkflowStepper({ currentPhase }) {
    const phases = [
        { id: 1, label: 'Sourcing', icon: '🌍', desc: 'Finding candidates on LinkedIn' },
        { id: 2, label: 'Deep Scrape', icon: '🕵️', desc: 'Scraping full profiles' },
        { id: 3, label: 'AI Analysis', icon: '🧠', desc: 'Scoring & ranking' },
    ]

    return (
        <div className="glass-card p-5">
            <div className="flex items-center justify-between relative">
                {/* Connector line */}
                <div className="absolute top-5 left-[60px] right-[60px] h-0.5 bg-slate-800" />
                <div
                    className="absolute top-5 left-[60px] h-0.5 bg-gradient-to-r from-brand-500 to-purple-500 transition-all duration-700 ease-out"
                    style={{
                        width:
                            currentPhase >= 3
                                ? 'calc(100% - 120px)'
                                : currentPhase >= 2
                                    ? 'calc(50% - 30px)'
                                    : '0%',
                    }}
                />

                {phases.map((phase) => {
                    const isActive = currentPhase === phase.id
                    const isDone = currentPhase > phase.id

                    return (
                        <div key={phase.id} className="flex flex-col items-center z-10 relative">
                            {/* Circle */}
                            <div
                                className={`w-10 h-10 rounded-full flex items-center justify-center text-lg transition-all duration-500
                  ${isDone
                                        ? 'bg-gradient-to-br from-brand-500 to-purple-600 shadow-lg shadow-brand-500/30 scale-100'
                                        : isActive
                                            ? 'bg-gradient-to-br from-brand-500 to-purple-600 shadow-lg shadow-brand-500/30 scale-110 animate-pulse-slow'
                                            : 'bg-slate-800 border border-slate-700'
                                    }`}
                            >
                                {isDone ? '✓' : phase.icon}
                            </div>

                            {/* Label */}
                            <span
                                className={`text-xs font-semibold mt-2 transition-colors duration-300
                  ${isActive ? 'text-brand-400' : isDone ? 'text-slate-300' : 'text-slate-600'}`}
                            >
                                {phase.label}
                            </span>

                            {/* Description */}
                            <span
                                className={`text-[10px] mt-0.5 transition-colors duration-300
                  ${isActive ? 'text-slate-400' : 'text-slate-700'}`}
                            >
                                {phase.desc}
                            </span>
                        </div>
                    )
                })}
            </div>
        </div>
    )
}
