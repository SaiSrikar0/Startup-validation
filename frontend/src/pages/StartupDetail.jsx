import { useEffect, useState } from 'react'
import { useParams, Link, useNavigate } from 'react-router-dom'
import { getStartup, deleteStartup } from '../services/api'
import StatusBadge from '../components/StatusBadge'
import Spinner from '../components/Spinner'
import toast from 'react-hot-toast'

const Section = ({ title, children }) => (
  <div className="card p-5 space-y-3">
    <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-wider">{title}</h3>
    {children}
  </div>
)

const Pill = ({ label }) => (
  <span className="text-xs bg-slate-800 border border-slate-700 text-slate-300 px-3 py-1 rounded-full">{label}</span>
)

export default function StartupDetail() {
  const { id } = useParams()
  const navigate = useNavigate()
  const [startup, setStartup] = useState(null)
  const [loading, setLoading]  = useState(true)

  useEffect(() => {
    getStartup(id)
      .then(({ data }) => setStartup(data))
      .catch(() => toast.error('Startup not found'))
      .finally(() => setLoading(false))
  }, [id])

  const handleDelete = async () => {
    if (!confirm(`Delete "${startup.company}"?`)) return
    try {
      await deleteStartup(id)
      toast.success('Startup deleted')
      navigate('/startups')
    } catch (e) {
      toast.error(e.message)
    }
  }

  if (loading) return <div className="flex justify-center py-20"><Spinner size="lg" /></div>
  if (!startup) return <div className="text-center py-20 text-slate-400">Startup not found.</div>

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between gap-4">
        <div>
          <Link to="/startups" className="text-xs text-slate-500 hover:text-slate-300 mb-2 inline-block">← Back to Startups</Link>
          <h1 className="text-2xl font-bold text-white">{startup.company}</h1>
          <div className="flex items-center gap-3 mt-2">
            <StatusBadge status={startup.status} />
            <span className="text-slate-500 text-sm">Founded {startup.year_founded}</span>
            {[startup.city, startup.country].filter(Boolean).length > 0 && (
              <span className="text-slate-500 text-sm">📍 {[startup.city, startup.country].filter(Boolean).join(', ')}</span>
            )}
          </div>
        </div>
        <div className="flex gap-2 shrink-0">
          <Link to={`/startups/${id}/edit`} className="btn-secondary text-sm py-2">Edit</Link>
          <button onClick={handleDelete} className="bg-red-900/40 hover:bg-red-900/60 border border-red-800 text-red-300 text-sm font-medium px-4 py-2 rounded-xl transition-colors">Delete</button>
        </div>
      </div>

      {/* Description */}
      {startup.description && (
        <Section title="About">
          <p className="text-slate-300 text-sm leading-relaxed">{startup.description}</p>
        </Section>
      )}

      {/* Categories */}
      {startup.categories.length > 0 && (
        <Section title="Categories">
          <div className="flex flex-wrap gap-2">
            {startup.categories.map(c => <Pill key={c} label={c} />)}
          </div>
        </Section>
      )}

      {/* Founders */}
      {startup.founders.length > 0 && (
        <Section title="Founders">
          <div className="flex flex-wrap gap-2">
            {startup.founders.map(f => <Pill key={f} label={f} />)}
          </div>
        </Section>
      )}

      {/* Investors */}
      {startup.investors.length > 0 && (
        <Section title="Investors">
          <div className="flex flex-wrap gap-2">
            {startup.investors.map(i => <Pill key={i} label={i} />)}
          </div>
        </Section>
      )}

      {/* Funding */}
      {startup.funding_rounds.length > 0 && (
        <Section title="Funding Rounds">
          <div className="flex flex-wrap gap-2">
            {startup.funding_rounds.map((r, i) => (
              <span key={i} className="text-xs bg-emerald-900/30 border border-emerald-800/50 text-emerald-300 px-3 py-1 rounded-full">{r}</span>
            ))}
          </div>
        </Section>
      )}

      {/* Actions */}
      <div className="flex gap-3">
        <Link to={`/predict`} className="btn-secondary text-sm flex-1 text-center py-3">
          🎯 Predict Similar Startup
        </Link>
        <Link to={`/compete`} className="btn-secondary text-sm flex-1 text-center py-3">
          ⚔️ Find Competitors
        </Link>
      </div>
    </div>
  )
}
