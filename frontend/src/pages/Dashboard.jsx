import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { getHealth } from '../services/api'
import Spinner from '../components/Spinner'

const StatCard = ({ label, value, sub, color = 'brand' }) => (
  <div className="card p-6 flex flex-col gap-1">
    <p className="text-slate-400 text-sm font-medium">{label}</p>
    <p className={`text-3xl font-bold text-${color}-400`}>{value}</p>
    {sub && <p className="text-slate-500 text-xs mt-1">{sub}</p>}
  </div>
)

const FeatureCard = ({ icon, title, desc, to, cta }) => (
  <Link to={to} className="card p-6 hover:border-brand-500/50 hover:bg-slate-800/50 transition-all duration-200 group block">
    <div className="text-3xl mb-4">{icon}</div>
    <h3 className="font-semibold text-white mb-2 group-hover:text-brand-400 transition-colors">{title}</h3>
    <p className="text-slate-400 text-sm leading-relaxed mb-4">{desc}</p>
    <span className="text-brand-400 text-sm font-medium group-hover:underline">{cta} →</span>
  </Link>
)

export default function Dashboard() {
  const [health, setHealth] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    getHealth()
      .then(({ data }) => setHealth(data))
      .catch(() => {})
      .finally(() => setLoading(false))
  }, [])

  return (
    <div className="space-y-10">
      {/* Hero */}
      <div className="relative overflow-hidden card p-10 bg-gradient-to-br from-brand-900/40 via-slate-900 to-slate-900">
        <div className="absolute top-0 right-0 w-96 h-96 bg-brand-500/5 rounded-full blur-3xl -translate-y-1/2 translate-x-1/2 pointer-events-none" />
        <div className="relative">
          <div className="inline-flex items-center gap-2 bg-brand-500/10 border border-brand-500/20 text-brand-400 text-xs font-semibold px-3 py-1.5 rounded-full mb-5">
            <span className="w-1.5 h-1.5 rounded-full bg-brand-400 animate-pulse" />
            AI-Powered Startup Intelligence
          </div>
          <h1 className="text-4xl font-extrabold text-white mb-3 leading-tight">
            Will your startup<br />
            <span className="text-brand-400">make it?</span>
          </h1>
          <p className="text-slate-400 max-w-lg text-base leading-relaxed mb-8">
            LaunchIQ analyzes your startup's profile against 600+ real companies and predicts your odds of success using data-driven insights.
          </p>
          <div className="flex items-center gap-3">
            <Link to="/predict" className="btn-primary text-sm">
              Predict My Success →
            </Link>
            <Link to="/startups" className="btn-secondary text-sm">
              Browse Startups
            </Link>
          </div>
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          label="Startups in Database"
          value={loading ? '—' : (health?.total_startups ?? '—')}
          sub="Loaded from cleaned dataset"
          color="brand"
        />
        <StatCard label="API Status" value={loading ? '—' : (health ? 'Online' : 'Offline')} sub="Backend health check" color={health ? 'emerald' : 'red'} />
        <StatCard label="Prediction Engine" value="Active" sub="Heuristic scoring model" color="violet" />
        <StatCard label="Competition Analysis" value="Active" sub="Category + location matching" color="amber" />
      </div>

      {/* Feature cards */}
      <div>
        <h2 className="text-lg font-semibold text-white mb-4">What you can do</h2>
        <div className="grid md:grid-cols-3 gap-4">
          <FeatureCard
            icon="🎯"
            title="Success Prediction"
            desc="Enter your startup details and get an instant success probability score with key contributing factors."
            to="/predict"
            cta="Try prediction"
          />
          <FeatureCard
            icon="⚔️"
            title="Competition Analysis"
            desc="Find your closest competitors from 600+ real startups based on category, location, and market overlap."
            to="/compete"
            cta="Find competitors"
          />
          <FeatureCard
            icon="🗂️"
            title="Startup Explorer"
            desc="Browse, search, filter, and manage the full startup database with CRUD operations."
            to="/startups"
            cta="Explore startups"
          />
        </div>
      </div>
    </div>
  )
}
