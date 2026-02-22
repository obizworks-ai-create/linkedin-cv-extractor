export default function StatusCard({ label, count, icon, color, active }) {
    return (
        <div className={`glass-card p-5 flex items-center justify-between transition-all duration-300
      ${active ? 'border-brand-500/40 bg-brand-500/5 shadow-brand-500/10' : ''}`}
        >
            <div>
                <div className="text-slate-500 text-xs font-semibold uppercase tracking-widest mb-1.5">
                    {label}
                </div>
                <div className={`text-3xl font-black tracking-tight ${color}`}>
                    {count}
                </div>
            </div>
            <div className={`text-3xl transition-all duration-300 ${active ? 'animate-pulse-slow scale-110' : 'grayscale opacity-40'}`}>
                {icon}
            </div>
        </div>
    )
}
