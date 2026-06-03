import { NavLink } from 'react-router-dom'

const links = [
  { to: '/',           label: 'Dashboard' },
  { to: '/predict',    label: 'Predict' },
  { to: '/compete',    label: 'Competition' },
  { to: '/startups',   label: 'Startups' },
]

export default function Navbar() {
  return (
    <nav className="fixed top-0 left-0 right-0 z-50 bg-slate-950/80 backdrop-blur border-b border-slate-800">
      <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
        <NavLink to="/" className="flex items-center gap-2.5 group">
          <div className="w-8 h-8 rounded-lg bg-brand-500 flex items-center justify-center text-white font-bold text-sm shadow-lg shadow-brand-500/30">
            L
          </div>
          <span className="font-bold text-lg text-white tracking-tight">LaunchIQ</span>
        </NavLink>

        <div className="flex items-center gap-1">
          {links.map(({ to, label }) => (
            <NavLink
              key={to}
              to={to}
              end={to === '/'}
              className={({ isActive }) =>
                `px-4 py-2 rounded-lg text-sm font-medium transition-all duration-200 ${
                  isActive
                    ? 'bg-brand-500/20 text-brand-400'
                    : 'text-slate-400 hover:text-white hover:bg-slate-800'
                }`
              }
            >
              {label}
            </NavLink>
          ))}
        </div>
      </div>
    </nav>
  )
}
